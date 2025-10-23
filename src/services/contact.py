from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db
from src import models as md
from src.config import constants as CNST
from src.config.enums import ContactStatus, SearchAllowedStatus
from src.exceptions import exceptions as exc
from src.services import _utils as utl
from src.services.profile import personal_values_already_set
from src.services.user_manager import UserManager
from src.tasks import send_contact_request_notification


async def get_contact_requests(
    *, my_user: db.User, a_session: AsyncSession
) -> tuple[md.ContactRequestsRead, str]:
    """
    Reads contact requests
    (contacts in status "requested by me"/"requested by other user"),
    and wraps to ContactRequestsRead.
    """
    contact_requests = await crud.read_user_contacts(
        my_user_id=my_user.id,
        statuses=[
            ContactStatus.REQUESTED_BY_ME,
            ContactStatus.REQUESTED_BY_OTHER,
        ],
        a_session=a_session,
    )
    incoming = []
    outgoing = []
    for cr in contact_requests:
        model = utl.contact_request_to_read_model(cr)
        if model.status == ContactStatus.REQUESTED_BY_OTHER:
            incoming.append(model)
        else:
            outgoing.append(model)
    message = (
        'Current contact requests.'
        if contact_requests
        else 'No contact requests.'
    )
    return md.ContactRequestsRead(
        incoming=incoming,
        outgoing=outgoing,
    ), message


async def get_ongoing_contacts(
    *,
    my_user: db.User,
    a_session: AsyncSession,
) -> tuple[list[md.ContactRead], str]:
    """Reads ongoing contacts, wraps to md.ContactRead."""
    contacts = await crud.read_user_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.ONGOING],
        a_session=a_session,
    )
    c_models = [utl.contact_to_read_model(contact=c) for c in contacts]
    message = 'Contacts.' if c_models else 'No active contacts.'
    return c_models, message


async def get_rejected_requests(
    *,
    my_user: db.User,
    a_session: AsyncSession,
) -> tuple[list[md.ContactRead], str]:
    """
    Reads rejected contacts ("contact requests"), wraps to md.ContactRead.
    """
    contacts = await crud.read_user_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.REJECTED_BY_ME],
        a_session=a_session,
    )
    c_models = [utl.contact_to_read_model(contact=c) for c in contacts]
    message = (
        'Rejected contact requests.'
        if c_models
        else 'No rejected contact requests.'
    )
    return c_models, message


async def get_cancelled_requests(
    *,
    my_user: db.User,
    a_session: AsyncSession,
) -> tuple[list[md.ContactRead], str]:
    """
    Reads cancelled contacts ("contact requests"), wraps to md.ContactRead.
    """
    contacts = await crud.read_user_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.CANCELLED_BY_ME],
        a_session=a_session,
    )
    c_models = [utl.contact_to_read_model(contact=c) for c in contacts]
    message = (
        'Cancelled contact requests.'
        if c_models
        else 'No cancelled contact requests.'
    )
    return c_models, message


async def get_blocked_contacts(
    *,
    my_user: db.User,
    a_session: AsyncSession,
) -> tuple[list[md.ContactRead], str]:
    """Reads blocked contacts, wraps to md.ContactRead."""
    contacts = await crud.read_user_contacts(
        my_user_id=my_user.id,
        statuses=[ContactStatus.BLOCKED_BY_ME],
        a_session=a_session,
    )
    c_models = [utl.contact_to_read_model(contact=c) for c in contacts]
    message = 'Blocked contacts.' if c_models else 'No blocked contacts.'
    return c_models, message


async def check_for_alike(
    *, my_user: db.User, a_session: AsyncSession
) -> tuple[list[md.OtherProfileRead] | None, str]:
    """
    Checks search_allowed_status and if personal values are set.
    Then uses reads recommendations for user.
    """
    ud = await crud.read_user_dynamics(user_id=my_user.id, a_session=a_session)
    if ud.search_allowed_status == SearchAllowedStatus.COOLDOWN:
        return None, (
            'Search for new Alike is temporarily unavailable.'
            ' It will be available again after a cooldown.'
        )
    if not await personal_values_already_set(
        my_user=my_user, a_session=a_session
    ):
        raise exc.NotFound('Personal values have not yet been set.')
    matches = await utl.get_recommendations(
        my_user_id=my_user.id, a_session=a_session
    )
    message = 'Matches found.' if matches else 'No matches for now.'
    return matches, message


async def agree_to_start(
    *,
    my_user: db.User,
    other_user_id: UUID,
    user_manager: UserManager,
    a_session: AsyncSession,
) -> tuple[md.ContactRead | None, str]:
    """
    Resets match_notifications_counter and unsuspends.

    If contact pair not yet exists:
    checks recommendations, creates pair of 'mirrored' contacts,
    notifies other user.

    If contact pair already exists:
    if other user already agreed - sets both
    UserDynamic.search_allowed_status to 'cooldown'
    and both Contact.status to 'ongoing'.

    If contact pair exists, but with unexpected statusees:
    responds accordingly.
    """
    await crud.reset_match_notifications_counter(
        user_id=my_user.id, a_session=a_session
    )
    await crud.unsuspend(user_id=my_user.id, a_session=a_session)
    contact_pair, created = await crud.create_or_read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        a_session=a_session,
    )
    contact_read_model = utl.contact_to_read_model(contact=contact_pair[0])
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
                a_session=a_session,
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
    await a_session.commit()
    return contact_read_model, message


async def cancel_contact_request(
    *,
    my_user: db.User,
    other_user_id: UUID,
    a_session: AsyncSession,
) -> tuple[md.ContactRequestsRead | None, str]:
    contact_pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        a_session=a_session,
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
    await a_session.commit()
    contact_requests_read, _ = await get_contact_requests(
        my_user=my_user,
        a_session=a_session,
    )
    message = 'Contact request cancelled.'
    return contact_requests_read, message


async def reject_contact_request(
    *,
    my_user: db.User,
    other_user_id: UUID,
    a_session: AsyncSession,
) -> tuple[md.ContactRequestsRead | None, str]:
    contact_pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        a_session=a_session,
    )
    if not contact_pair:
        raise exc.NotFound(
            (
                f'Contact not found for {my_user.id=}, {other_user_id=}, '
                f'status={ContactStatus.REQUESTED_BY_OTHER}.'
            )
        )
    if contact_pair[0].status != ContactStatus.REQUESTED_BY_OTHER:
        raise exc.BadRequest('Only incoming contact requests can be rejected.')
    contact_pair[0].status = ContactStatus.REJECTED_BY_ME
    contact_pair[1].status = ContactStatus.REJECTED_BY_OTHER
    await a_session.commit()
    contact_requests_read, _ = await get_contact_requests(
        my_user=my_user,
        a_session=a_session,
    )
    return contact_requests_read, 'Contact request rejected.'


async def block_contact(
    *,
    my_user: db.User,
    other_user_id: UUID,
    a_session: AsyncSession,
) -> tuple[list[md.ContactRead], str]:
    contact_pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        a_session=a_session,
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
    await a_session.commit()
    contact_models, _ = await get_ongoing_contacts(
        my_user=my_user, a_session=a_session
    )
    return contact_models, 'Contact blocked.'


async def unblock_contact(
    my_user: db.User, other_user_id: UUID, a_session: AsyncSession
) -> tuple[list[md.ContactRead], str]:
    pair = await crud.read_contact_pair(
        my_user_id=my_user.id,
        other_user_id=other_user_id,
        a_session=a_session,
    )
    if not pair:
        raise exc.NotFound('Requested contact not found.')
    if pair[0].status != ContactStatus.BLOCKED_BY_ME:
        raise exc.BadRequest(f'Requested contact status is {pair[0].status}')
    pair[0].status = pair[1].status = ContactStatus.ONGOING
    await a_session.commit()
    contact_models, _ = await get_ongoing_contacts(
        my_user=my_user, a_session=a_session
    )
    return contact_models, 'Contact unblocked.'


async def get_contact_profile(
    *,
    my_user: db.User,
    other_user_id: UUID,
    a_session: AsyncSession,
) -> tuple[md.OtherProfileRead, str]:
    contacts = await crud.read_user_contacts(
        my_user_id=my_user.id, other_user_id=other_user_id, a_session=a_session
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
        a_session=a_session,
    )
    if other_mp is None:
        raise exc.ServerError('Moral profile not found.')
    other_prof_read_md = md.OtherProfileRead.model_validate(other_mp._asdict())
    return other_prof_read_md, 'Other user profile.'
