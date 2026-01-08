from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.config import constants as CNST
from src.config.enums import ContactStatus, SearchAllowedStatus
from src.db.user_and_profile import User
from src.exceptions import exceptions as exc
from src.models.contact_n_message import (
    ContactRead,
    ContactRequestRead,
    OtherProfileRead,
)
from src.services import _utils as _utils
from src.services.profile import personal_values_already_set
from src.services.user_manager import UserManager
from src.tasks import send_contact_request_notification


async def get_contact_requests(
    *, my_user: User, asession: AsyncSession
) -> tuple[list[ContactRequestRead], str]:
    """
    Reads contact requests
    (contacts in status "requested by me"/"requested by other user"),
    returns a list with message].
    """
    contact_tuples = await crud.read_contacts(
        my_user_id=my_user.id,
        statuses=[
            ContactStatus.REQUESTED_BY_ME,
            ContactStatus.REQUESTED_BY_OTHER,
        ],
        asession=asession,
    )

    models = [
        _utils.contact_request_to_read_model(contact=ct[0])
        for ct in contact_tuples
    ]
    message = (
        'Current contact requests.'
        if contact_tuples
        else 'No contact requests.'
    )
    return models, message


async def get_ongoing_contacts(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[list[ContactRead], str]:
    """
    Reads ongoing contacts,
    returns as tuple[ContactRead schema, info message].
    """
    tuples = await crud.read_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.ONGOING],
        asession=asession,
    )
    contact_read_models = [
        _utils.contact_to_read_model(contact=t[0], unread_msg_count=t[1])
        for t in tuples
    ]
    message = 'Contacts.' if contact_read_models else 'No active contacts.'
    return contact_read_models, message


async def get_contacts_and_requests(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[list[ContactRead], list[ContactRequestRead], str]:
    """
    Reads:
    1. active contacts with unread messages counts,
    2. contact requests.
    Returns with servise message.
    """
    contacts = await crud.read_contacts_rich(
        my_user_id=my_user.id,
        statuses=[
            ContactStatus.ONGOING,
            ContactStatus.REQUESTED_BY_ME,
            ContactStatus.REQUESTED_BY_OTHER,
        ],
        asession=asession,
    )
    message = (
        'Contacts and requests.'
        if contacts
        else 'No active contacts or contact requests.'
    )
    contact_models = []
    request_models = []
    for contact in contacts:
        model = _utils.rich_contact_to_read_model(contact=contact)
        if contact.status == ContactStatus.ONGOING:
            contact_models.append(model)
        else:
            request_models.append(model)
    return contact_models, request_models, message


async def get_rejected_requests(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[list[ContactRead], str]:
    """
    Reads rejected (by 'me') contacts ('contact requests').
    Returns as tuple[ContactRead schema, info message].
    """
    tuples = await crud.read_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.REJECTED_BY_ME],
        asession=asession,
    )
    c_models = [_utils.contact_to_read_model(contact=t[0]) for t in tuples]
    message = (
        'Rejected contact requests.'
        if c_models
        else 'No rejected contact requests.'
    )
    return c_models, message


async def get_cancelled_requests(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[list[ContactRead], str]:
    """
    Reads cancelled (by 'me') contacts ('contact requests'),
    returns as tuple[ContactRead schema, info message].
    """
    tuples = await crud.read_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.CANCELLED_BY_ME],
        asession=asession,
    )
    c_models = [_utils.contact_to_read_model(contact=t[0]) for t in tuples]
    message = (
        'Cancelled contact requests.'
        if c_models
        else 'No cancelled contact requests.'
    )
    return c_models, message


async def get_blocked_contacts(
    *,
    my_user: User,
    asession: AsyncSession,
) -> tuple[list[ContactRead], str]:
    """Reads blocked contacts, returns as ContactRead schema."""
    tuples = await crud.read_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.BLOCKED_BY_ME],
        asession=asession,
    )
    c_models = [_utils.contact_to_read_model(contact=t[0]) for t in tuples]
    message = 'Blocked contacts.' if c_models else 'No blocked contacts.'
    return c_models, message


async def check_for_alike(
    *, my_user: User, asession: AsyncSession
) -> tuple[list[OtherProfileRead] | None, str]:
    """
    Checks search_allowed_status and if personal values are set.
    Then reads recommendations for user.
    """
    ud = await crud.read_user_dynamics(user_id=my_user.id, asession=asession)
    if ud.search_allowed_status == SearchAllowedStatus.COOLDOWN:
        return None, (
            'Search for new contact is temporarily unavailable.'
            ' It will be available again after a cooldown.'
        )
    if not await personal_values_already_set(
        my_user=my_user, asession=asession
    ):
        raise exc.NotFound('Personal values have not yet been set.')
    matches = await _utils.get_recommendations(
        my_user_id=my_user.id, asession=asession
    )
    message = 'Matches found.' if matches else 'No matches for now.'
    return matches, message


async def agree_to_start(
    *,
    my_user: User,
    other_user_id: UUID,
    user_manager: UserManager,
    asession: AsyncSession,
) -> tuple[ContactRead | None, str]:
    """
    Resets match_notifications_counter and unsuspends search_allowed_status.

    If contact pair not yet exists:
    checks recommendations, creates pair of 'mirrored' contacts,
    notifies other user.

    If contact pair already exists:
    if other user already confirmed - sets both
    UserDynamic.search_allowed_status to 'cooldown'
    and both Contact.status to 'ongoing'.

    If contact pair exists, but with unexpected statusees:
    responds accordingly.
    """
    if my_user.id == other_user_id:
        raise exc.BadRequest("Current user's id passed as target.")
    requested_profile = await crud.read_other_profile(
        my_user_id=my_user.id, other_user_id=other_user_id, asession=asession
    )
    if requested_profile is None or requested_profile.similarity_score == 0:
        raise exc.NotFound(f'Requested user not found: {other_user_id}.')
    await crud.reset_match_notifications_counter(
        user_id=my_user.id, asession=asession
    )
    await crud.unsuspend(user_id=my_user.id, asession=asession)
    contact_pair, created = await crud.create_or_read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    contact_read_model = _utils.contact_to_read_model(contact=contact_pair[0])
    match contact_pair[0].status, created:
        case ContactStatus.REQUESTED_BY_ME, True:
            other_user = await user_manager.get(id=other_user_id)
            send_contact_request_notification.delay(email=other_user.email)
            message = 'Accepted. Waiting for the other user.'
        case ContactStatus.REQUESTED_BY_ME, False:
            message = 'Waiting for the other user.'
        case ContactStatus.REQUESTED_BY_OTHER, False:
            contact_pair[0].status = contact_pair[1].status = (
                ContactStatus.ONGOING.value
            )
            await crud.set_to_cooldown(
                user_ids=[my_user.id, other_user_id],
                asession=asession,
            )
            message = 'Chat started!'
        case ContactStatus.CANCELLED_BY_ME, False:
            contact_pair[0].status = ContactStatus.REQUESTED_BY_ME.value
            contact_pair[1].status = ContactStatus.REQUESTED_BY_OTHER.value
            message = 'Accepted. Waiting for the other user.'
        case ContactStatus.REJECTED_BY_ME, False:
            contact_pair[0].status = ContactStatus.REQUESTED_BY_ME.value
            contact_pair[1].status = ContactStatus.REQUESTED_BY_OTHER.value
            other_user = await user_manager.get(id=other_user_id)
            send_contact_request_notification.delay(email=other_user.email)
            message = 'Accepted. Waiting for the other user.'
        case _, _:
            message = f'Contact status is: {contact_pair[0].status}.'
    await asession.commit()
    return contact_read_model, message


async def cancel_contact_request(
    *,
    my_user: User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[list[ContactRequestRead], str]:
    """
    Puts contact ('contact request') to cancelled status
    Only allowed for sent requests.
    Returns as list with info message
    """
    contact_pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if not contact_pair:
        raise exc.NotFound(
            (
                f'Contact not found for {my_user.id=}, {other_user_id=}, '
                f'status={ContactStatus.REQUESTED_BY_ME}.'
            )
        )
    if contact_pair[0].status != ContactStatus.REQUESTED_BY_ME:
        raise exc.BadRequest(
            'Only outgoing contact requests can be cancelled.'
        )
    contact_pair[0].status = ContactStatus.CANCELLED_BY_ME
    contact_pair[1].status = ContactStatus.CANCELLED_BY_OTHER
    await asession.commit()
    contact_requests_read, _ = await get_contact_requests(
        my_user=my_user,
        asession=asession,
    )
    message = 'Contact request cancelled.'
    return contact_requests_read, message


async def reject_contact_request(
    *,
    my_user: User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[list[ContactRequestRead], str]:
    """
    Puts contact ('contact request') to rejected status.
    Only allowed for received requests.
    Returns new list of contact requests with service message.
    """
    contact_pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if not contact_pair:
        raise exc.NotFound(
            (
                f'Contact not found for {my_user.id=}, {other_user_id=}, '
                f'status={ContactStatus.REQUESTED_BY_OTHER}.'
            )
        )
    if contact_pair[0].status != ContactStatus.REQUESTED_BY_OTHER:
        raise exc.BadRequest('Only received contact requests can be rejected.')
    contact_pair[0].status = ContactStatus.REJECTED_BY_ME
    contact_pair[1].status = ContactStatus.REJECTED_BY_OTHER
    await asession.commit()
    contact_requests_read, _ = await get_contact_requests(
        my_user=my_user,
        asession=asession,
    )
    return contact_requests_read, 'Contact request rejected.'


async def block_contact(
    *,
    my_user: User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[list[ContactRead], str]:
    """
    Blocks contact (puts to 'blocked' status).
    Only allowed for ongoing contacts.
    Returns as tuple[list[ContactRead schemas], info message]
    """
    contact_pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if not contact_pair:
        raise exc.NotFound(
            (f'Contact not found for {my_user.id=}, {other_user_id=}.')
        )
    if contact_pair[0].status not in (CNST.BLOCKABLE_CONTACT_STATUSES):
        raise exc.BadRequest(
            (
                'You can only block contacts with the following statuses: '
                f'{", ".join(CNST.BLOCKABLE_CONTACT_STATUSES)}.'
            )
        )
    contact_pair[0].status = ContactStatus.BLOCKED_BY_ME
    contact_pair[1].status = ContactStatus.BLOCKED_BY_OTHER
    await asession.commit()
    contact_models, _ = await get_ongoing_contacts(
        my_user=my_user, asession=asession
    )
    return contact_models, 'Contact blocked.'


async def unblock_contact(
    my_user: User, other_user_id: UUID, asession: AsyncSession
) -> tuple[list[ContactRead], str]:
    """
    Unblocks contact (puts to 'ongoing' status).
    Only allowed for contacts blocked by me.
    Returns as tuple[list[ContactRead schemas], info message]
    """
    pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if not pair:
        raise exc.NotFound('Requested contact not found.')
    if pair[0].status != ContactStatus.BLOCKED_BY_ME:
        raise exc.BadRequest(f'Requested contact status is {pair[0].status}')
    pair[0].status = pair[1].status = ContactStatus.ONGOING
    await asession.commit()
    contact_models, _ = await get_ongoing_contacts(
        my_user=my_user, asession=asession
    )
    return contact_models, 'Contact unblocked.'


async def get_contact_profile(
    *,
    my_user: User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[OtherProfileRead, str]:
    """
    Reads profile of a conact user.
    Returns as tuple[OtherProfileRead schema, info message].
    """
    contacts = await crud.read_contacts(
        my_user_id=my_user.id, other_user_id=other_user_id, asession=asession
    )
    if not contacts:
        raise exc.NotFound(f'Contact not found for user_id {other_user_id}')
    if len(contacts) > 1:
        raise exc.ServerError(
            (
                'Inconsistent number of contacts found '
                f'for {my_user.id}, {other_user_id}'
            )
        )
    other_mp = await crud.read_other_profile(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if other_mp is None:
        raise exc.ServerError('Moral profile not found.')
    other_prof_read_md = OtherProfileRead.model_validate(other_mp._asdict())
    return other_prof_read_md, 'Other user profile.'
