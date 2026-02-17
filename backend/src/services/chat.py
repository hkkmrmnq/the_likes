import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

import redis.asyncio as redis_a
from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

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
    def __init__(self, websocket: WebSocket, last_received: float = 0):
        self.ws = websocket
        self.last_received = last_received


class ChatManager:
    def __init__(self, pubsub_url: str = CFG.REDIS_PUBSUB_URL):
        self.connections: dict[UUID, Connection] = {}
        self.offline_messages: dict[UUID, list] = {}
        self.message_counts: dict[UUID, list[float]] = {}
        self._lock = ReentrantLock()
        self._disconnect_inactive_task = None
        self._pubsub_url = pubsub_url
        self._redis_a: Redis | None = None
        self._pubsub: PubSub | None = None
        self._listen_task = None

    @property
    async def redis(self) -> Redis:
        """Lazy redis initialization."""
        if self._redis_a is None:
            self._redis_a = await redis_a.from_url(self._pubsub_url)
        return self._redis_a

    @property
    async def pubsub(self) -> PubSub:
        """Lazy pubsub initialization."""
        if self._pubsub is None:
            if self._redis_a is None:
                self._redis_a = await redis_a.from_url(self._pubsub_url)
            self._pubsub = self._redis_a.pubsub()
        return self._pubsub

    async def _listen_for_messages(self):
        """Listen for messages from other workers."""
        pubsub = await self.pubsub
        async for message in pubsub.listen():
            if 'receiver_id' not in message:
                logger.error('pubsub: no receiver_id in message, skipped.')
                continue
            await self.validate_and_send_payload(
                payload=json.loads(message),
                target_user_id=message['receiver_id'],
            )

    async def _disconnect_inactive(self):
        try:
            while True:
                current_time = time.time()
                async with self._lock:
                    for user_id, conn in self.connections.items():
                        elapsed = current_time - conn.last_received
                        if elapsed > CFG.CHAT.INACTIVITY_MAX_SECONDS:
                            await self.remove_connection(
                                user_id=user_id,
                                code=status.WS_1000_NORMAL_CLOSURE,
                            )
                await asyncio.sleep(CFG.CHAT.CLOSE_INACTIVE_EVERY)
        except Exception as e:
            error_msg = e.args[0] if len(e.args) > 0 else 'Unknown'
            logger.error(f'disconnect_inactive error: {error_msg=}')

    async def create_tasks(self):
        self._disconnect_inactive_task = asyncio.create_task(
            self._disconnect_inactive()
        )
        self._listen_task = asyncio.create_task(self._listen_for_messages())

    async def _cancel_task(
        self, task: asyncio.Task | None, name: str = 'task'
    ):
        """Safely cancel and await a task"""
        if not task:
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_msg = e.args[0] if len(e.args) > 0 else 'Unknown'
            logger.error(f'Error while cancelling {name}: {error_msg=}')

    async def remove_tasks(self):
        """Clean up all tasks and connections"""

        # Stop receiving new messages
        if self._pubsub:
            await self._pubsub.unsubscribe()

        # Cancel all tasks
        await self._cancel_task(
            self._disconnect_inactive_task, 'disconnect_inactive'
        )
        await self._cancel_task(self._listen_task, 'listen_task')

        # Close connection
        if self._redis_a:
            await self._redis_a.close()

    async def add_connection(
        self, *, user_id: UUID, websocket: WebSocket
    ) -> bool:
        async with self._lock:
            if len(self.connections) > CFG.CHAT.MAX_CONNECTIONS:
                logger.warning('MAX_CONNECTIONS exceeded.')
                return False
            await websocket.accept()
            if user_id not in self.connections:
                connection = Connection(
                    websocket=websocket, last_received=time.time()
                )
                self.connections[user_id] = connection
            else:
                logger.info(
                    'add_connection: user_id in self.active_connections'
                )
            pubsub = await self.pubsub
            await pubsub.subscribe(f'chat:{user_id}')
            await self.send_queued_validated_payloads(user_id=user_id)
            return True

    async def remove_connection(self, *, user_id: UUID, code: int):
        pubsub = await self.pubsub
        await pubsub.unsubscribe(f'chat:{user_id}')
        async with self._lock:
            if user_id not in self.connections:
                logger.info(
                    f'remove_connection: user {user_id} not in connections'
                )
                return
            connection = self.connections[user_id]
            try:
                await connection.ws.close(code=code)
                logger.info(f'User {user_id} disconnected.')
            except RuntimeError:
                logger.info(f'remove_connection: already closed? ({user_id=})')
                self.connections.pop(user_id)
            except ConnectionError:
                logger.warning(
                    f'remove_connection: Network error? ({user_id=})'
                )
            except Exception as e:
                error_msg = e.args[0] if len(e.args) > 0 else 'Unknown'
                logger.error(
                    'ws.close attempt failed '
                    f'({connection.ws.application_state=}) '
                    f'{error_msg=}'
                )

    async def validate_and_send_payload(
        self,
        *,
        payload: dict,
        target_user_id: UUID,
    ):
        try:
            schema = sch.ChatPayload.model_validate(payload)
            valid_json = schema.model_dump_json()
            async with self._lock:
                if target_user_id in self.connections:
                    connection = self.connections[target_user_id]
                    await connection.ws.send_text(valid_json)
                    if isinstance(schema.related_content, sch.MessageRead):
                        async with asession_factory() as asession:
                            await crud.mark_as_read(
                                sender_id=schema.related_content.sender_id,
                                receiver_id=schema.related_content.receiver_id,
                                up_to=schema.related_content.created_at,
                                asession=asession,
                            )
                            await asession.commit()
                else:
                    redis = await self.redis
                    await redis.publish(f'chat:{target_user_id}', valid_json)
        except ValidationError as e:
            logger.error(f'Schema ValidationError(s): {len(e.errors())}')
            for i, error in enumerate(e.errors()):
                logger.error(f'\nError {i + 1}:')
                logger.error(
                    f'  Field: {" -> ".join(str(loc) for loc in error["loc"])}'
                )
                logger.error(f'Message: {error["msg"]}')
                logger.error(f'Type: {error["type"]}')
                logger.error(f'Input: {error.get("input", "N/A")}')
        except Exception as e:
            error_msg = e.args[0] if len(e.args) > 0 else 'Unknown'
            logger.error(
                f'validate_and_send_payload general exception: '
                f'{target_user_id=} {error_msg=}'
            )
            await self.remove_connection(
                user_id=target_user_id,
                code=status.WS_1011_INTERNAL_ERROR,
            )

    async def enqueue_payload(self, *, payload: dict, target_user_id: UUID):
        if 'payload_type' not in payload:
            logger.error('queue_payload error: no payload_type in payload.')
            return
        if payload['payload_type'] == ENM.ChatPayloadType.PING:
            return
        if target_user_id not in self.offline_messages:
            self.offline_messages[target_user_id] = []
        queue = self.offline_messages[target_user_id]
        if len(queue) > CFG.CHAT.MAX_QUEUE:
            del queue[0]
        queue.append(payload)

    async def update_last_received(self, user_id: UUID):
        async with self._lock:
            if user_id not in self.connections:
                logger.info(
                    f'update_last_received - no {user_id=} in connections'
                )
                return
            self.connections[user_id].last_received = time.time()

    async def send_queued_validated_payloads(self, *, user_id: UUID):
        if (
            user_id not in self.offline_messages
            or not self.offline_messages[user_id]
        ):
            return
        messages = self.offline_messages.pop(user_id)
        for msg in messages:
            await self.validate_and_send_payload(
                payload=msg,
                target_user_id=user_id,
            )

    async def check_rate_limit(self, user_id: UUID) -> bool:
        now = time.time()
        if user_id not in self.message_counts:
            self.message_counts[user_id] = []

        self.message_counts[user_id] = [
            ts
            for ts in self.message_counts[user_id]
            if now - ts < CFG.CHAT.RATE_PERIOD_SECONDS
        ]

        if len(self.message_counts[user_id]) >= CFG.CHAT.RATE_NUMBER:
            return False

        self.message_counts[user_id].append(now)
        return True

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
            # Confirm to sender
            await self.validate_and_send_payload(
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
            # Forward to recipient
            await self.validate_and_send_payload(
                payload={
                    'payload_type': ENM.ChatPayloadType.NEW,
                    'related_content': msg_cnt,
                    'timestamp': received_timestamp,
                },
                target_user_id=msg_cnt.receiver_id,
            )
        except Exception as e:
            # Report error to sender
            error_message = 'Unexpected server error.'
            if isinstance(e, exc.BadRequest | exc.NotFound | exc.ServerError):
                error_message = e.args[0]
            error_msg = e.args[0] if len(e.args) > 0 else 'Unknown'
            logger.error(f'{error_msg=}')
            await self.validate_and_send_payload(
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
                await self.validate_and_send_payload(
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
        await self.validate_and_send_payload(
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
                    if user_id not in self.connections:
                        return
                    lst_rcvd = self.connections[user_id].last_received
                    if now.timestamp() - lst_rcvd > interval:
                        await self.validate_and_send_payload(
                            payload={
                                'payload_type': ENM.ChatPayloadType.PING,
                                'related_content': sch.PingPongDetail(
                                    ping_timestamp=None
                                ),
                                'timestamp': sch.format_to_zod_timestamp(now),
                            },
                            target_user_id=user_id,
                        )
                        # logger.debug('ping sent')
            except Exception:
                logger.error('send_pings general exception.')
                break

    async def manage_chat(
        self,
        *,
        current_user: db.User,
        websocket: WebSocket,
    ) -> str:
        ok = await self.add_connection(
            user_id=current_user.id, websocket=websocket
        )
        if not ok:
            return 'MAX_CONNECTIONS exceeded.'
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
                if not await self.check_rate_limit(current_user.id):
                    logger.warning('Rate limit exceeded.')
                    await self.remove_connection(
                        user_id=current_user.id,
                        code=status.WS_1008_POLICY_VIOLATION,
                    )
                    return 'Rate limit exceeded.'
                await self.update_last_received(user_id=current_user.id)
                if datetime.now() > expiration:
                    await self.remove_connection(
                        user_id=current_user.id,
                        code=status.WS_1008_POLICY_VIOLATION,
                    )
                    return 'Access token expired.'
                payload = await websocket.receive_json()
                await self.process_payload(
                    current_user_id=current_user.id, payload=payload
                )

        except WebSocketDisconnect:
            await self.remove_connection(
                user_id=current_user.id, code=status.WS_1000_NORMAL_CLOSURE
            )
            return 'Normal closure.'
        except Exception as e:
            logger.error(
                f'WebSocket general Exception: {current_user.id=}, {e.args[0]}'
            )
            await self.remove_connection(
                user_id=current_user.id, code=status.WS_1011_INTERNAL_ERROR
            )
            return 'Internal error.'
        # finally:
        #     send_pings_task.cancel()


chat_manager = ChatManager()
