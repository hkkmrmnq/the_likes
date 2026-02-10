from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, db
from src import schemas as sch
from src.config import CNST, ENM
from src.exceptions import exc

from . import utils as utl


async def get_contacts_and_requests(
    *,
    current_user: db.User,
    asession: AsyncSession,
) -> tuple[sch.ActiveContactsAndRequests, str]:
    """
    Reads:
    1. active contacts with unread messages counts,
    2. contact requests.
    Returns as tuple of sch.ActiveContactsAndRequests and info message.
    """
    contacts = await crud.read_contacts(
        my_user_id=current_user.id,
        statuses=[
            ENM.ContactStatus.ONGOING,
            ENM.ContactStatus.REQUESTED_BY_ME,
            ENM.ContactStatus.REQUESTED_BY_OTHER,
        ],
        asession=asession,
    )
    contacts = contacts
    message = (
        'Contacts and requests.'
        if contacts
        else 'No active contacts or contact requests.'
    )
    contact_models = []
    request_models = []
    for contact in contacts:
        model = utl.rich_contact_to_schema(contact=contact)
        if contact.status == ENM.ContactStatus.ONGOING:
            contact_models.append(model)
        else:
            request_models.append(model)
    return sch.ActiveContactsAndRequests(
        active_contacts=contact_models, contact_requests=request_models
    ), message


async def get_rejected_requests(
    *,
    current_user: db.User,
    asession: AsyncSession,
) -> tuple[list[sch.ContactRead], str]:
    """
    Reads rejected (by 'me') contacts ('contact requests').
    Returns as tuple[ContactRead schema, info message].
    """
    contacts = await crud.read_contacts(
        my_user_id=current_user.id,
        statuses=[ENM.ContactStatus.REJECTED_BY_ME],
        asession=asession,
    )
    c_models = [utl.rich_contact_to_schema(contact=c) for c in contacts]
    message = (
        'Rejected contact requests.'
        if c_models
        else 'No rejected contact requests.'
    )
    return c_models, message


async def get_cancelled_requests(
    *,
    current_user: db.User,
    asession: AsyncSession,
) -> tuple[list[sch.ContactRead], str]:
    """
    Reads cancelled (by 'me') contacts ('contact requests'),
    returns as tuple[ContactRead schema, info message].
    """
    contacts = await crud.read_contacts(
        my_user_id=current_user.id,
        statuses=[ENM.ContactStatus.CANCELLED_BY_ME],
        asession=asession,
    )
    c_models = [utl.rich_contact_to_schema(contact=c) for c in contacts]
    message = (
        'Cancelled contact requests.'
        if c_models
        else 'No cancelled contact requests.'
    )
    return c_models, message


async def get_blocked_contacts(
    *,
    current_user: db.User,
    asession: AsyncSession,
) -> tuple[list[sch.ContactRead], str]:
    """Reads blocked contacts, returns as ContactRead schema."""
    contacts = await crud.read_contacts(
        my_user_id=current_user.id,
        statuses=[ENM.ContactStatus.BLOCKED_BY_ME],
        asession=asession,
    )
    c_models = [utl.rich_contact_to_schema(contact=c) for c in contacts]
    message = 'Blocked contacts.' if c_models else 'No blocked contacts.'
    return c_models, message


async def check_for_alike(
    *, current_user: db.User, asession: AsyncSession
) -> tuple[list[sch.RecommendationRead], str]:
    """
    Checks search_allowed_status and if personal values are set.
    Then reads recommendations for user.
    """
    ud = await crud.read_user_dynamics(
        user_id=current_user.id, asession=asession
    )
    if ud.search_allowed_status == ENM.SearchAllowedStatus.COOLDOWN:
        return [], CNST.COOLDOWN_RESPONSE_MESSAGE
    if not await utl.personal_values_already_set(
        my_user=current_user, asession=asession
    ):
        return [], 'Personal values have not yet been set.'
    recommendations = await utl.get_recommendations(
        my_user_id=current_user.id, asession=asession
    )
    contacts = await crud.read_contacts(
        my_user_id=current_user.id, asession=asession
    )
    contacts_user_ids = [c.other_user_id for c in contacts]
    matches = [
        r for r in recommendations if r.user_id not in contacts_user_ids
    ]
    message = 'Matches found.' if matches else 'No matches for now.'
    return matches, message


async def get_conts_n_reqsts_n_recoms(
    *,
    current_user: db.User,
    asession: AsyncSession,
) -> tuple[sch.ContsNReqstsNRecoms, str]:
    conts_n_reqsts, _ = await get_contacts_and_requests(
        current_user=current_user, asession=asession
    )
    recoms, msg = await check_for_alike(
        current_user=current_user, asession=asession
    )
    return sch.ContsNReqstsNRecoms(
        recommendations=recoms,
        active_contacts=conts_n_reqsts.active_contacts,
        contact_requests=conts_n_reqsts.contact_requests,
    ), msg


async def agree_to_start(
    *,
    current_user: db.User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[sch.ActiveContactsAndRequests, str]:
    """
    Resets match_notifications_counter and unsuspends search_allowed_status.

    If contact pair not yet exists:
    checks recommendations, creates pair of 'mirrored' contacts,
    notifies other user.

    If contact pair already exists:
    if other user already confirmed - sets both
    search_allowed_status to 'cooldown'
    and both Contact.status to 'ongoing'.

    If contact pair exists, but with unexpected statusees:
    responds accordingly.

    Returns as tuple of sch.ActiveContactsAndRequests and info message.
    """
    if current_user.id == other_user_id:
        raise exc.BadRequest("Current user's id passed as target.")
    requested_profile = await crud.read_other_profile(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if requested_profile is None or requested_profile.similarity == 0:
        raise exc.NotFound(f'Requested user not found: {other_user_id}.')
    await crud.reset_match_notifications_counter(
        user_id=current_user.id, asession=asession
    )
    await crud.unsuspend(user_id=current_user.id, asession=asession)
    (my_contact, _), created = await utl.create_or_get_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    match my_contact.status, created:
        case ENM.ContactStatus.REQUESTED_BY_ME, _:
            message = 'Accepted. Waiting for the other user.'
        case ENM.ContactStatus.REQUESTED_BY_OTHER, False:
            await utl.update_contact_pair(
                my_user_id=current_user.id,
                other_user_id=other_user_id,
                my_contact_status=ENM.ContactStatus.ONGOING,
                asession=asession,
            )
            await crud.set_to_cooldown(
                user_ids=[current_user.id, other_user_id],
                asession=asession,
            )
            message = 'Chat started!'
        case (
            ENM.ContactStatus.CANCELLED_BY_ME
            | ENM.ContactStatus.REJECTED_BY_ME,
            False,
        ):
            await utl.update_contact_pair(
                my_user_id=current_user.id,
                other_user_id=other_user_id,
                my_contact_status=ENM.ContactStatus.REQUESTED_BY_ME,
                asession=asession,
            )
            message = 'Accepted. Waiting for the other user.'
        case _, _:
            message = f'Contact status is: {my_contact.status}.'
    await asession.commit()
    contacts_and_requests, _ = await get_contacts_and_requests(
        current_user=current_user, asession=asession
    )
    return contacts_and_requests, message


async def cancel_contact_request(
    *,
    current_user: db.User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[sch.ActiveContactsAndRequests, str]:
    """
    Puts contact to cancelled status
    Only allowed for contacts with status REQUESTED_BY_ME.
    Returns as tuple of sch.ActiveContactsAndRequests and info message.
    """
    contact_pair, _ = await utl.get_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
        raise_not_found=True,
    )
    my_contact, _ = contact_pair
    if my_contact.status != ENM.ContactStatus.REQUESTED_BY_ME:
        raise exc.BadRequest(
            'Only outgoing contact requests can be cancelled.'
        )
    await utl.update_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        my_contact_status=ENM.ContactStatus.CANCELLED_BY_ME,
        asession=asession,
    )
    await asession.commit()
    active_contacts_and_requests, _ = await get_contacts_and_requests(
        current_user=current_user,
        asession=asession,
    )
    return active_contacts_and_requests, 'Contact request cancelled.'


async def reject_contact_request(
    *,
    current_user: db.User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[sch.ActiveContactsAndRequests, str]:
    """
    Puts contact ('contact request') to rejected status.
    Only allowed for received requests.
    Returns as tuple of sch.ActiveContactsAndRequests and info message.
    """
    contact_pair, _ = await utl.get_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
        raise_not_found=True,
    )
    my_contact, _ = contact_pair
    if my_contact.status != ENM.ContactStatus.REQUESTED_BY_OTHER:
        raise exc.BadRequest('Only received contact requests can be rejected.')
    await utl.update_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        my_contact_status=ENM.ContactStatus.REJECTED_BY_ME,
        asession=asession,
    )
    await asession.commit()
    active_contacts_and_requests, _ = await get_contacts_and_requests(
        current_user=current_user,
        asession=asession,
    )
    return active_contacts_and_requests, 'Contact request rejected.'


async def block_contact(
    *,
    current_user: db.User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[sch.ActiveContactsAndRequests, str]:
    """
    Blocks contact (puts to 'blocked' status).
    Only allowed for ongoing contacts.
    Returns as tuple of sch.ActiveContactsAndRequests and info message.
    """
    contact_pair, _ = await utl.get_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
        raise_not_found=True,
    )
    my_contact, _ = contact_pair
    if my_contact.status not in (CNST.BLOCKABLE_CONTACT_STATUSES):
        raise exc.BadRequest(
            (
                'You can only block contacts with the following statuses: '
                f'{", ".join(CNST.BLOCKABLE_CONTACT_STATUSES)}.'
            )
        )
    await utl.update_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        my_contact_status=ENM.ContactStatus.BLOCKED_BY_ME,
        asession=asession,
    )
    await asession.commit()
    active_contacts_and_requests, _ = await get_contacts_and_requests(
        current_user=current_user, asession=asession
    )
    return active_contacts_and_requests, 'Contact blocked.'


async def unblock_contact(
    current_user: db.User, other_user_id: UUID, asession: AsyncSession
) -> tuple[sch.ActiveContactsAndRequests, str]:
    """
    Unblocks contact (puts to 'ongoing' status).
    Only allowed for contacts blocked by me.
    Returns as tuple of sch.ActiveContactsAndRequests and info message.
    """
    contact_pair, _ = await utl.get_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
        raise_not_found=True,
    )
    my_contact, _ = contact_pair
    if my_contact.status != ENM.ContactStatus.BLOCKED_BY_ME:
        raise exc.BadRequest(
            f'Requested contact status is {my_contact.status}. '
            'Only contacts in status BLOCKED_BY_ME can be unblocked.'
        )
    await utl.update_contact_pair(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        my_contact_status=ENM.ContactStatus.ONGOING,
        asession=asession,
    )
    await asession.commit()
    active_contacts_and_requests, _ = await get_contacts_and_requests(
        current_user=current_user, asession=asession
    )
    return active_contacts_and_requests, 'Contact unblocked.'


async def get_other_profile(
    *,
    current_user: db.User,
    other_user_id: UUID,
    asession: AsyncSession,
) -> tuple[sch.RecommendationRead, str]:
    """
    Reads profile of a conact user.
    Returns as tuple[OtherProfileRead schema, info message].
    """
    contacts = await crud.read_contacts(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if not contacts:
        recommendations = await crud.read_user_recommendations(
            my_user_id=current_user.id,
            other_user_id=other_user_id,
            asession=asession,
        )
        if not recommendations:
            raise exc.NotFound(
                'Requested user not found in contacts/recommendations.'
            )
    if len(contacts) > 1:
        raise exc.ServerError(
            (
                'Inconsistent number of contacts found '
                f'for {current_user.id}, {other_user_id}'
            )
        )
    other_profile = await crud.read_other_profile(
        my_user_id=current_user.id,
        other_user_id=other_user_id,
        asession=asession,
    )
    if other_profile is None:
        raise exc.ServerError('Moral profile not found.')
    return sch.RecommendationRead.model_validate(
        other_profile
    ), 'Other user profile.'


async def get_additional_contacts_options(
    current_user: db.User, asession: AsyncSession
) -> tuple[sch.AdditionalContactsOptions, str]:
    contacts = await crud.read_contacts(
        my_user_id=current_user.id,
        statuses=[
            ENM.ContactStatus.REJECTED_BY_ME,
            ENM.ContactStatus.CANCELLED_BY_ME,
            ENM.ContactStatus.BLOCKED_BY_ME,
        ],
        asession=asession,
    )
    c_schemas = [utl.rich_contact_to_schema(contact=c) for c in contacts]
    message = (
        'Rejected contact requests.'
        if c_schemas
        else 'No rejected contact requests.'
    )
    options_schema = sch.AdditionalContactsOptions(
        cancelled_requests=[
            c
            for c in c_schemas
            if c.status == ENM.ContactStatus.CANCELLED_BY_ME
        ],
        rejected_requests=[
            c
            for c in c_schemas
            if c.status == ENM.ContactStatus.REJECTED_BY_ME
        ],
        blocked_contacts=[
            c for c in c_schemas if c.status == ENM.ContactStatus.BLOCKED_BY_ME
        ],
    )
    return options_schema, message
