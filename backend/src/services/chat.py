import asyncio
import json
import os
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
from src import exceptions as exc
from src import schemas as sch
from src import services as srv
from src.config import CFG, ENM
from src.logger import async_catch, logger
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
        self,
        *,
        websocket: WebSocket,
        last_received: float = 0,
        expiration: datetime,
    ):
        self.ws = websocket
        self.last_received = last_received
        self.expiration = expiration


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
            if self._redis_a is None:
                raise exc.ServerError('ChatManager._redis_a is None.')
            self._pubsub = self._redis_a.pubsub()
        return self._pubsub

    async def _listen_for_payloads(self):
        """Listen for messages from other workers."""
        pubsub = await self.pubsub
        await pubsub.subscribe('keepalive')
        async for payload in pubsub.listen():
            if payload['type'] != 'message':
                continue
            channel = payload['channel']
            if isinstance(channel, bytes):
                channel = channel.decode('utf-8')
            target_user_id = UUID(channel.replace('ws:', ''))
            chat_payload = payload.get('data')
            if isinstance(chat_payload, bytes):
                chat_payload = json.loads(payload['data'].decode('utf-8'))
            await self.validate_and_send_payload(
                payload=chat_payload, target_user_id=target_user_id
            )

    @async_catch(to_raise=False)
    async def _disconnect_inactive(self):
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

    async def start_up(self):
        self._disconnect_inactive_task = asyncio.create_task(
            self._disconnect_inactive()
        )
        self._listen_task = asyncio.create_task(self._listen_for_payloads())

    @async_catch(to_raise=False)
    async def _cancel_task(
        self, task: asyncio.Task | None, name: str = 'task'
    ):
        if not task:
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        # except Exception as e:
        #     error_msg = exc.get_error_msg(e)
        #     logger.error(f'Error while cancelling {name}: {error_msg=}')

    async def shut_down(self):
        if self._pubsub:
            await self._pubsub.unsubscribe()

        await self._cancel_task(
            self._disconnect_inactive_task, 'disconnect_inactive'
        )
        await self._cancel_task(self._listen_task, 'listen_task')

        if self._redis_a:
            await self._redis_a.aclose()

    async def add_connection(
        self, *, user_id: UUID, websocket: WebSocket
    ) -> bool:
        async with self._lock:
            if len(self.connections) > CFG.CHAT.MAX_CONNECTIONS:
                logger.warning('MAX_CONNECTIONS exceeded.')
                return False
            await websocket.accept()
            if user_id not in self.connections:
                expiration = datetime.now() + timedelta(
                    seconds=CFG.JWT_ACCESS_LIFETIME_MINUTES * 60
                )
                connection = Connection(
                    websocket=websocket,
                    last_received=time.time(),
                    expiration=expiration,
                )
                self.connections[user_id] = connection
            pubsub = await self.pubsub
            await pubsub.subscribe(f'ws:{user_id}')
            await self.send_queued_validated_payloads(user_id=user_id)
            return True

    @async_catch(to_raise=False)
    async def remove_connection(self, *, user_id: UUID, code: int):
        logger.info(f'{datetime.now()} remove_connection: {code=}')
        pubsub = await self.pubsub
        await pubsub.unsubscribe(f'ws:{user_id}')
        async with self._lock:
            if user_id not in self.connections:
                return
            connection = self.connections[user_id]
            try:
                await connection.ws.close(code=code)
            except RuntimeError:
                self.connections.pop(user_id)
            except ConnectionError:
                logger.warning(
                    f'worker {os.getpid()}: remove_connection: '
                    f'Network error? ({user_id=})'
                )
            # except Exception:
            #     logger.error(f'({connection.ws.application_state=}) ')

    async def check_connection_expiration(self, user_id: UUID) -> bool:
        """
        Returns True if connection is not yet expired.
        Returns False if connection expired or no connection for this user_id.
        """
        async with self._lock:
            if user_id not in self.connections:
                return False
            return datetime.now() < self.connections[user_id].expiration

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
                    if isinstance(schema.related_content, sch.MessageRead):
                        redis = await self.redis
                        await redis.publish(f'ws:{target_user_id}', valid_json)

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
            error_msg = exc.get_error_msg(e)
            logger.error(
                f'validate_and_send_payload general exception: '
                f'{target_user_id=} {error_msg=}'
            )
            await self.remove_connection(
                user_id=target_user_id,
                code=status.WS_1011_INTERNAL_ERROR,
            )

    async def update_last_received(self, user_id: UUID):
        async with self._lock:
            if user_id not in self.connections:
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

    @async_catch(to_raise=False)
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
                    'payload_type': ENM.ChatPayloadType.MSG_SENT,
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
                    'payload_type': ENM.ChatPayloadType.NEW_MSG,
                    'related_content': msg_cnt,
                    'timestamp': received_timestamp,
                },
                target_user_id=msg_cnt.receiver_id,
            )

        except Exception as e:
            # Report error to sender
            await self.validate_and_send_payload(
                payload={
                    'payload_type': ENM.ChatPayloadType.MSG_ERROR,
                    'related_content': sch.MessageError(
                        error='Something went wrong.'
                    ),
                    'timestamp': received_timestamp,
                },
                target_user_id=current_user_id,
            )
            raise e

    async def process_payload(
        self, current_user_id: UUID, payload: dict
    ) -> str:
        data = sch.ChatPayload.model_validate(payload)
        match data.payload_type:
            case ENM.ChatPayloadType.CREATE_MSG:
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
                        'related_content': sch.HeartbeatDetail(
                            origin=ENM.BeatOrigin.BACK
                        ),
                        'timestamp': sch.get_now_timestamp_for_zod(),
                    },
                    target_user_id=current_user_id,
                )
                return 'ping received'
            case ENM.ChatPayloadType.PONG:
                return 'pong received'
        error_msg = 'Unexpected chat payload type'
        await self.validate_and_send_payload(
            payload={
                'payload_type': ENM.ChatPayloadType.MSG_ERROR,
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
                                'related_content': sch.HeartbeatDetail(
                                    origin=ENM.BeatOrigin.BACK
                                ),
                                'timestamp': sch.format_to_zod_timestamp(now),
                            },
                            target_user_id=user_id,
                        )
            except Exception:
                logger.error('send_pings general exception.')
                break

    @async_catch(to_raise=False)
    async def manage_chat(
        self,
        *,
        current_user: db.User,
        websocket: WebSocket,
    ) -> str:
        user_id = current_user.id
        ok = await self.add_connection(user_id=user_id, websocket=websocket)
        if not ok:
            return 'MAX_CONNECTIONS exceeded.'

        # send_pings_task = asyncio.create_task(
        #     self._send_pings(
        #         user_id=user_id,
        #         interval=CFG.WS_PING_INTERVAL_SECONDS,
        #     )
        # )
        try:
            while True:
                if not await self.check_rate_limit(user_id):
                    logger.warning('Rate limit exceeded.')
                    await self.remove_connection(
                        user_id=user_id,
                        code=status.WS_1008_POLICY_VIOLATION,
                    )
                    return 'Rate limit exceeded.'
                if not await self.check_connection_expiration(user_id):
                    await self.remove_connection(
                        user_id=user_id,
                        code=status.WS_1008_POLICY_VIOLATION,
                    )
                    return 'Access token expired.'
                await self.update_last_received(user_id=user_id)
                payload = await websocket.receive_json()
                await self.process_payload(
                    current_user_id=user_id, payload=payload
                )

        except WebSocketDisconnect:
            await self.remove_connection(
                user_id=user_id, code=status.WS_1000_NORMAL_CLOSURE
            )
            logger.info('CLIENT DISCONNECTED')
            return 'Normal closure.'
        except Exception as e:
            await self.remove_connection(
                user_id=user_id, code=status.WS_1011_INTERNAL_ERROR
            )
            logger.error('WS_1011_INTERNAL_ERROR')
            raise e
        # finally:
        #     send_pings_task.cancel()


chat_manager = ChatManager()
