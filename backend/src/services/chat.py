import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    status,
)

from src import containers as cnt
from src import crud, db
from src import schemas as sch
from src import services as srv
from src.config import CFG, ENM
from src.exceptions import exc
from src.logger import logger
from src.sessions import asession_factory


class ReentrantLock:
    """Reentrant asyncio lock"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._depth = 0

    async def __aenter__(self):
        current_task = asyncio.current_task()
        if self._task is not current_task:
            await self._lock.acquire()
            self._task = current_task
        self._depth += 1
        return self

    async def __aexit__(self, *args):
        self._depth -= 1
        if self._depth == 0:
            self._task = None
            self._lock.release()


class Connection:
    def __init__(
        self, websocket: WebSocket, last_received: datetime | None = None
    ):
        self.ws = websocket
        self.last_received = last_received


class ChatManager:
    def __init__(self):
        self.active_connections: dict[UUID, Connection] = {}
        self._lock = ReentrantLock()
        self.offline_messages: dict[UUID, list] = {}

    async def add_connection(
        self, *, user_id: UUID, websocket: WebSocket
    ) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id in self.active_connections:
                logger.info(
                    'add_connection: user_id in self.active_connections'
                )
                await self.remove_connection(
                    user_id=user_id, code=status.WS_1000_NORMAL_CLOSURE
                )
            connection = Connection(websocket=websocket)
            self.active_connections[user_id] = connection
            logger.info(f'User {user_id} connected.')
            await self.send_offline_messages(user_id=user_id)

    async def remove_connection(self, *, user_id: UUID, code: int):
        async with self._lock:
            if user_id not in self.active_connections:
                logger.info(
                    f'remove_connection: user {user_id} not in connections'
                )
                return
            connection = self.active_connections[user_id]
            try:
                await connection.ws.close(code=code)
                logger.info(f'User {user_id} disconnected.')
            except RuntimeError:
                logger.info(f'remove_connection: already closed? ({user_id=})')
                self.active_connections.pop(user_id)
            except ConnectionError:
                logger.warning(
                    f'remove_connection: Network error? ({user_id=})'
                )
            except Exception:
                logger.error(
                    'ws.close attempt failed '
                    f'({connection.ws.application_state=})'
                )

    async def send_payload(
        self,
        *,
        payload: dict | cnt.MessageRead,
        target_user_id: UUID,
    ):
        try:
            data = sch.ChatPayload.model_validate(payload)
            async with self._lock:
                if target_user_id in self.active_connections:
                    connection = self.active_connections[target_user_id]
                    await connection.ws.send_json(data.model_dump(mode='json'))
                    if isinstance(data.related_content, sch.MessageRead):
                        async with asession_factory() as asession:
                            await crud.mark_as_read(
                                sender_id=data.related_content.sender_id,
                                receiver_id=data.related_content.receiver_id,
                                up_to=data.related_content.created_at,
                                asession=asession,
                            )
                            await asession.commit()
                else:
                    if data.payload_type == ENM.ChatPayloadType.PING:
                        return
                    if target_user_id not in self.offline_messages:
                        self.offline_messages[target_user_id] = []
                    self.offline_messages[target_user_id].append(payload)
        except Exception as e:
            logger.error(f'Error sending to {target_user_id}: {e}')
            await self.remove_connection(
                user_id=target_user_id,
                code=status.WS_1011_INTERNAL_ERROR,
            )

    async def update_last_received(self, user_id: UUID):
        async with self._lock:
            if user_id not in self.active_connections:
                logger.info(
                    f'update_last_received - no {user_id=} in connections'
                )
                return
            self.active_connections[user_id].last_received = datetime.now(
                timezone.utc
            )

    async def send_offline_messages(self, *, user_id: UUID):
        if user_id in self.offline_messages and self.offline_messages[user_id]:
            messages = self.offline_messages.pop(user_id)
        else:
            async with asession_factory() as asession:
                messages = await crud.read_all_unread_messages_to_user(
                    receiver_id=user_id, asession=asession
                )
            for msg in messages:
                await self.send_payload(
                    payload=msg,
                    target_user_id=user_id,
                )

    async def process_chat_message(
        self,
        msg_data: cnt.MessageCreate,
        current_user_id: UUID,
    ):
        received_timestamp = sch.get_now_timestamp_for_zod()
        try:
            async with asession_factory() as asession:
                await srv.add_message(
                    current_user_id=current_user_id,
                    data=msg_data,
                    asession=asession,
                )
                await asession.commit()
                msg_cnt = await crud.read_last_message(
                    sender_id=current_user_id,
                    receiver_id=msg_data.receiver_id,
                    asession=asession,
                )
                if msg_cnt is None:
                    raise exc.ServerError(
                        (
                            'Message not found after creation.'
                            f'sender_id={current_user_id}, '
                            f'receiver_id={msg_data.receiver_id}.'
                        )
                    )
            # Forward to recipient
            logger.info(f'Forward to recipient: {msg_cnt=}')
            await self.send_payload(
                payload={
                    'payload_type': ENM.ChatPayloadType.NEW,
                    'related_content': msg_cnt,
                    'timestamp': received_timestamp,
                },
                target_user_id=msg_cnt.receiver_id,
            )
            # Confirm to sender
            await self.send_payload(
                payload={
                    'payload_type': ENM.ChatPayloadType.SENT,
                    'related_content': {
                        'receiver_id': msg_cnt.receiver_id,
                        'client_id': msg_data.client_id,
                        'created_at': msg_cnt.created_at,
                        'time': msg_cnt.time,
                    },
                    'timestamp': received_timestamp,
                },
                target_user_id=current_user_id,
            )
        except Exception as error:
            # Report error to sender
            error_message = 'Unexpected server error.'
            if isinstance(
                error, exc.BadRequest | exc.NotFound | exc.ServerError
            ):
                error_message = error.args[0]
            logger.error(error.args[0])
            logger.error(error.__traceback__)
            await self.send_payload(
                payload={
                    'payload_type': ENM.ChatPayloadType.ERROR,
                    'related_content': sch.MessageError(error=error_message),
                    'timestamp': received_timestamp,
                },
                target_user_id=current_user_id,
            )

    async def process_payload(
        self, current_user_id: UUID, payload: dict
    ) -> str:
        data = sch.ChatPayload.model_validate(payload)
        match data.payload_type:
            case ENM.ChatPayloadType.CREATE:
                client_message = data.related_content
                if not isinstance(client_message, sch.MessageCreate):
                    raise exc.ServerError(
                        'Wrong message format after schema validation.'
                    )
                msg_data = cnt.MessageCreate(
                    sender_id=current_user_id,
                    receiver_id=client_message.receiver_id,
                    text=client_message.text,
                    client_id=client_message.client_id,
                )
                await self.process_chat_message(
                    msg_data=msg_data,
                    current_user_id=current_user_id,
                )
                return 'New message processed.'
            case ENM.ChatPayloadType.PING:
                await self.send_payload(
                    payload={
                        'payload_type': ENM.ChatPayloadType.PONG,
                        'related_content': sch.PingPongDetail(
                            ping_timestamp=data.timestamp
                        ),
                        'timestamp': sch.get_now_timestamp_for_zod(),
                    },
                    target_user_id=current_user_id,
                )
                return 'ping received'
            case ENM.ChatPayloadType.PONG:
                msg = 'pong received'
                logger.info(msg)
                return 'pong received'
        error_msg = 'Unexpected chat payload type'
        await self.send_payload(
            payload={
                'payload_type': ENM.ChatPayloadType.ERROR,
                'related_content': sch.MessageError(error=error_msg),
                'timestamp': sch.get_now_timestamp_for_zod(),
            },
            target_user_id=current_user_id,
        )
        return error_msg

    async def _send_pings(self, *, user_id: UUID, interval: int):
        while True:
            await asyncio.sleep(interval)
            try:
                now = datetime.now(timezone.utc)
                async with self._lock:
                    if user_id not in self.active_connections:
                        return
                    lst_rcvd = self.active_connections[user_id].last_received
                    td_interval = timedelta(seconds=interval)
                    if not lst_rcvd or now - lst_rcvd > td_interval:
                        await self.send_payload(
                            payload={
                                'payload_type': ENM.ChatPayloadType.PING,
                                'related_content': sch.PingPongDetail(
                                    ping_timestamp=None
                                ),
                                'timestamp': sch.format_to_zod_timestamp(now),
                            },
                            target_user_id=user_id,
                        )
            except Exception:
                logger.error('send_pings general exception.')
                break

    async def manage_chat(
        self,
        *,
        current_user: db.User,
        websocket: WebSocket,
    ) -> str:
        await self.add_connection(user_id=current_user.id, websocket=websocket)
        expiration = datetime.now() + timedelta(
            seconds=CFG.JWT_ACCESS_LIFETIME_MINUTES * 60
        )
        # send_pings_task = asyncio.create_task(
        #     self._send_pings(
        #         user_id=current_user.id,
        #         interval=CFG.WS_PING_INTERVAL_SECONDS,
        #     )
        # )
        try:
            while True:
                payload = await websocket.receive_json()
                await self.update_last_received(user_id=current_user.id)
                if datetime.now() > expiration:
                    logger.info('token expired')
                    await self.remove_connection(
                        user_id=current_user.id,
                        code=status.WS_1008_POLICY_VIOLATION,
                    )
                    return 'Access token expired.'
                await self.process_payload(
                    current_user_id=current_user.id, payload=payload
                )

        except WebSocketDisconnect:
            logger.info('WebSocketDisconnect - Normal closure.')
            await self.remove_connection(
                user_id=current_user.id, code=status.WS_1000_NORMAL_CLOSURE
            )
            return 'Normal closure.'
        except Exception as e:
            logger.error(
                f'WebSocket general Exception: {current_user.id=}, {e}'
            )
            await self.remove_connection(
                user_id=current_user.id, code=status.WS_1011_INTERNAL_ERROR
            )
            return 'Internal error.'
        # finally:
        #     send_pings_task.cancel()


chat_manager = ChatManager()
