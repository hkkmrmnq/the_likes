from datetime import datetime, timedelta
from uuid import UUID

from celery import Celery
from celery.schedules import crontab

from src import crud
from src import schemas as sch
from src.config import CFG, CNST, ENM
from src.logger import logger, sync_catch
from src.redis_client import redis_client, redis_pubsub_client
from src.sessions import sync_engine, sync_session_factory

celery_app = Celery(
    'scheduler_celery',
    broker=CFG.REDIS_MAIN_URL,
    result_expires=timedelta(days=1),
)


def send_email(*, email_to: str, subject: str, content: str) -> None:
    message = f'TO: {email_to}\nSUBJECT: {subject}\nCONTENT: {content}'
    logger.info(f'{message}')


#     message = EmailMessage()
#     message['From'] = CNF.EMAIL_APP_EMAIL
#     message['To'] = email_to
#     message['Subject'] = subject
#     message.set_content(content)

#     await aiosmtplib.send(
#         message,
#         hostname=SMTP_SERVER,
#         port=SMTP_PORT,
#         username=CNF.EMAIL_APP_EMAIL,
#         password=CNF.EMAIL_APP_PASSWORD,
#     )


@celery_app.task
@sync_catch(to_raise=True)
def send_email_confirmation_code(*, email: str, code: str):
    send_email(
        email_to=email,
        subject='Welcome to The Likes!',
        content=(
            'To verify your email copy this code to our page '
            'and click "Confirm email".\n'
            f'{code}'
        ),
    )


@celery_app.task
@sync_catch(to_raise=True)
def send_password_reset_token(*, email: str, token: str):
    send_email(
        email_to=email,
        subject='Password reset requested.',
        content=(
            'Someone requested password reset for account, '
            'that registered with this email.\n'
            'If it was not you - ignore this message.\n'
            'If you did request password reset - '
            'copy this token to field:\n\n'
            f'{token}'
        ),
    )


@celery_app.task
@sync_catch(to_raise=True)
def send_password_reset_email_notification(*, email: str):
    send_email(
        email_to=email,
        subject='Password changed.',
        content='Password for your account have been changed.',
    )


@celery_app.task
@sync_catch(to_raise=True)
def send_contact_request_email_notification(*, email: str):
    send_email(
        email_to=email,
        subject='Chat request from user.',
        content='A user is ready to chat!',
    )


@celery_app.task
def recommendations_chain():
    """Chain the tasks"""
    chain = (
        refresh_materialized_views.s()
        | notify_matches.s().set(countdown=60)
        | update_match_notification_counters.s().set(countdown=60)
    )
    return chain.apply_async()


@celery_app.task(ignore_result=True)
@sync_catch(to_raise=True)
def send_match_email_notification(*, email: str, user_id: str):
    """
    Used when match found for user.
    After sending email adds user id to redis for further processing.
    """
    send_email(
        email_to=email,
        subject='Match found!',
        content='Similar user found!',
    )
    redis_client.rpush(  # type: ignore
        CNST.MATCH_NOTIFIED_REDIS_KEY, user_id
    )
    redis_client.expire(
        CNST.MATCH_NOTIFIED_REDIS_KEY,
        timedelta(days=1),
    )


@celery_app.task
@sync_catch(to_raise=True)
def refresh_materialized_views():
    """
    Task to refresh moral_profiles and recommendations
    materialized views.
    """
    with sync_engine.connect().execution_options(
        isolation_level='AUTOCOMMIT'
    ) as connection:
        connection.execute(crud.sql.refresh_moral_profiles)
        connection.execute(crud.sql.vacuum_moral_profiles)
        connection.execute(crud.sql.refresh_all_recommendations)
        connection.execute(crud.sql.vacuum_all_recommendations)
        connection.execute(crud.sql.refresh_limited_recommendations)
        connection.execute(crud.sql.vacuum_limited_recommendations)


@celery_app.task
@sync_catch(to_raise=True)
def notify_matches(previous_task_result=None):
    """
    Reads limited_recommendations MV,
    publishes new recommendations to redis for chat managers to send it
    and sets 'match found' email notification tasks.
    """
    with sync_session_factory() as session:
        users_to_notify = crud.read_users_to_notify_of_match(ssession=session)
    for user_to_notify in users_to_notify:
        schema = sch.ChatPayload(
            payload_type=ENM.ChatPayloadType.NEW_RECOMM,
            related_content=sch.RecommendationRead(
                user_id=user_to_notify.match_user_id,
                name=user_to_notify.match_name,
                similarity=user_to_notify.similarity,
                distance=user_to_notify.distance,
            ),
            timestamp=sch.get_now_timestamp_for_zod(),
        )
        valid_json = schema.model_dump_json()
        key = f'ws:{user_to_notify.user_id}'
        redis_pubsub_client.publish(key, valid_json)
        send_match_email_notification.delay(
            email=user_to_notify.email, user_id=str(user_to_notify.user_id)
        )


@celery_app.task
@sync_catch(to_raise=True)
def update_match_notification_counters(previous_task_result=None):
    """
    Reads 'match found'-notified users ids from redis
    and increments UserDynamic match_notified.
    """
    str_ids = redis_client.lrange(  # type: ignore
        CNST.MATCH_NOTIFIED_REDIS_KEY, 0, -1
    )
    assert isinstance(str_ids, list)
    user_uuids = [UUID(s) for s in str_ids]
    with sync_session_factory() as session:
        crud.increment_match_notification_counters(
            users_ids=user_uuids, ssession=session
        )
        session.commit()
    redis_client.delete(CNST.MATCH_NOTIFIED_REDIS_KEY)


@celery_app.task
@sync_catch(to_raise=True)
def end_cooldowns():
    """
    Sets back to 'ok' UserDynamic.search_allowed_status if it's 'coooldown'
    and CFG.COOLDOWN_DURATION time passed.
    """
    update_after = datetime.now() - timedelta(
        hours=CFG.COOLDOWN_DURATION_HOURS
    )
    with sync_session_factory() as session:
        crud.end_cooldowns(update_after=update_after, ssession=session)
        session.commit()


@celery_app.task
@sync_catch(to_raise=True)
def suspend():
    with sync_session_factory() as session:
        crud.suspend(session=session)
        session.commit()


ntfy_matches_h, ntfy_matches_m = CFG.NOTIFY_MATCHES_AT_HOUR_MIN
upd_cntrs_h, updt_cntrs_m = CFG.UPDATE_MATCH_NOTIFICATION_COUNTERS_AT_HOUR_MIN
suspend_h, suspend_m = CFG.SUSPEND_AT_HOUR_MIN

celery_app.conf.beat_schedule = {
    'recommendations_chain': {
        'task': 'src.tasks.recommendations_chain',
        'schedule': timedelta(
            hours=CFG.REFRESH_MATERIALIZED_VIEWS_EVERY_HOURS
        ),
    },
    'end_cooldowns': {
        'task': 'src.tasks.end_cooldowns',
        'schedule': timedelta(hours=CFG.END_COOLDOWNS_EVERY_HOURS),
    },
    'suspend': {
        'task': 'src.tasks.suspend',
        'schedule': crontab(hour=suspend_h, minute=suspend_m),
    },
}
