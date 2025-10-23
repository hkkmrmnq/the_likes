from datetime import datetime, timedelta
from uuid import UUID

import redis
from celery import Celery

from src import crud
from src.config import constants as CNST
from src.crud import sql
from src.sessions import s_session_factory

redis_client = redis.Redis(
    host='localhost', port=6379, db=0, decode_responses=True
)

celery_app = Celery(
    'scheduler_celery',
    broker='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    result_expires=timedelta(days=1),
)


def send_email(*, email_to: str, subject: str, content: str) -> None:
    print(f'TO: {email_to}\nSUBJECT: {subject}\nCONTENT: {content}')


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
def send_email_confirmation_token(*, email: str, token: str):
    send_email(
        email_to=email,
        subject='Welcome to The Likes!',
        content=(
            'To verify your email copy this token to our page '
            'and click "Confirm email".\n\n'
            f'{token}'
        ),
    )


@celery_app.task
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
def send_password_reset_notification(*, email: str):
    send_email(
        email_to=email,
        subject='Password changed.',
        content='Password for your account have been changed.',
    )


@celery_app.task
def send_contact_request_notification(*, email: str):
    send_email(
        email_to=email,
        subject='Chat request from user.',
        content='A user is ready to chat!',
    )


@celery_app.task(ignore_result=True)
def send_match_notification(*, user_data: dict):
    try:
        send_email(
            email_to=user_data['email'],
            subject='Match found!',
            content='Similar user found!',
        )
        redis_client.rpush(
            CNST.MATCH_NOTIFIED_REDIS_KEY, str(user_data['user_id'])
        )
        redis_client.expire(
            CNST.MATCH_NOTIFIED_REDIS_KEY,
            timedelta(days=1),
        )
    except Exception as e:
        raise e


@celery_app.task
def refresh_materialized_views():
    """
    Task to refresh moral_profiles and recommendations
    materialized views.
    """

    try:
        with s_session_factory() as session:
            session.execute(sql.refresh_moral_profiles)
            session.commit()
        with s_session_factory() as session:
            session.execute(sql.refresh_recommendations)
            session.commit()

    except Exception as e:
        raise e

    return 'Materialized views refreshed.'


@celery_app.task
def update_match_notification_counters():
    str_ids = redis_client.lrange(CNST.MATCH_NOTIFIED_REDIS_KEY, 0, -1)
    assert isinstance(str_ids, list)
    user_uuids = [UUID(s) for s in str_ids]
    with s_session_factory() as session:
        crud.update_match_notification_counters(
            users_ids=user_uuids, s_session=session
        )
        session.commit()
    redis_client.delete(CNST.MATCH_NOTIFIED_REDIS_KEY)


@celery_app.task
def notify_matches():
    with s_session_factory() as session:
        models = crud.read_users_to_notify_of_match(s_session=session)
    for model in models:
        send_match_notification.delay(user_data=model.model_dump())
    return 'notify_match tasks added to queue.'


@celery_app.task
def end_cooldowns():
    update_after = datetime.now() - CNST.COOLDOWN_DURATION
    with s_session_factory() as session:
        crud.end_cooldowns(update_after=update_after, s_session=session)
        session.commit()

    return 'Cooldowns managed.'


@celery_app.task
def suspend():
    with s_session_factory() as s_session:
        crud.suspend(s_session=s_session)
        s_session.commit()
    return 'Suspended.'


celery_app.conf.beat_schedule = {
    'refresh_materialized_views': {
        'task': 'src.tasks.refresh_materialized_views',
        'schedule': CNST.REFRESH_MATERIALIZED_VIEWS_EVERY,
    },
    'notify_matches': {
        'task': 'src.tasks.notify_matches',
        'schedule': CNST.NOTIFY_MATCHES_AT,
    },
    'update_match_notification_counters': {
        'task': 'src.tasks.update_match_notification_counters',
        'schedule': CNST.UPDATE_MATCH_NOTIFICATION_COUNTERS_AT,
    },
    'end_cooldowns': {
        'task': 'src.tasks.end_cooldowns',
        'schedule': CNST.END_COOLDOWNS_EVERY,
    },
    'suspend': {
        'task': 'src.tasks.suspend',
        'schedule': CNST.SUSPEND_AT,
    },
}
