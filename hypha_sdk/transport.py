"""
HYPHA Message Transport — Pure Python (asyncio TCP)
Replaces the Node.js Hyperswarm-based transport.
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict

from nacl.signing import SigningKey, VerifyKey

from .protocol import Message, MessageType

log = logging.getLogger(__name__)


class MessageTransport:
    """Pure-Python TCP message transport for agent-to-agent messaging."""

    def __init__(self, agent_id: str, private_key: Optional[bytes] = None):
        self.agent_id = agent_id
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_messages: asyncio.Queue = asyncio.Queue()

        if private_key:
            self.signing_key = SigningKey(private_key[:32])
        else:
            self.signing_key = SigningKey.generate()
        self.verify_key = self.signing_key.verify_key

        self._server: Optional[asyncio.Server] = None
        self._listening = False

    # ── Signing ──────────────────────────────────────────────

    def sign_message(self, message: Message) -> Message:
        unsigned = Message(
            type=message.type, sender=message.sender,
            recipient=message.recipient, payload=message.payload,
            timestamp=message.timestamp, signature=None,
        )
        signed = self.signing_key.sign(unsigned.to_bytes())
        message.signature = signed.signature.hex()
        return message

    def verify_message(self, message: Message, sender_verify_key: VerifyKey) -> bool:
        if not message.signature:
            return False
        try:
            unsigned = Message(
                type=message.type, sender=message.sender,
                recipient=message.recipient, payload=message.payload,
                timestamp=message.timestamp, signature=None,
            )
            sender_verify_key.verify(unsigned.to_bytes(), bytes.fromhex(message.signature))
            return True
        except Exception:
            return False

    # ── Send / Receive ───────────────────────────────────────

    async def send_message(self, message: Message, host: str = "127.0.0.1", port: int = 8469) -> bool:
        """Send a signed message over TCP."""
        signed = self.sign_message(message)
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(signed.to_bytes())
            writer.write_eof()
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            log.warning(f"Send failed: {e}")
            return False

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = await reader.read(65536)
        writer.close()
        if not data:
            return
        try:
            message = Message.from_bytes(data)
            await self.handle_message(message)
        except Exception as e:
            log.error(f"Error handling incoming message: {e}")

    async def start_listening(self, host: str = "0.0.0.0", port: int = 8469):
        """Start TCP server for incoming messages."""
        self._server = await asyncio.start_server(self._handle_connection, host, port)
        self._listening = True
        log.info(f"Listening for messages on {host}:{port}")
        async with self._server:
            await self._server.serve_forever()

    def register_handler(self, message_type: MessageType, handler: Callable[[Message], None]):
        self.message_handlers[message_type.value] = handler

    async def handle_message(self, message: Message):
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                log.error(f"Handler error for {message.type}: {e}")
        else:
            log.debug(f"No handler for message type: {message.type}")

    # ── Convenience senders ──────────────────────────────────

    async def send_task_request(self, recipient, escrow_id, task_description, amount, deadline, **kw) -> bool:
        from .protocol import TaskRequestMessage
        msg = TaskRequestMessage(escrow_id=escrow_id, task_description=task_description,
                                 amount=amount, deadline=deadline).to_message(self.agent_id, recipient)
        return await self.send_message(msg)

    async def send_task_response(self, recipient, escrow_id, accepted, estimated_completion=None, message_text=None) -> bool:
        from .protocol import TaskResponseMessage
        msg = TaskResponseMessage(escrow_id=escrow_id, accepted=accepted,
                                  estimated_completion=estimated_completion, message=message_text
                                  ).to_message(self.agent_id, recipient)
        return await self.send_message(msg)

    async def send_task_complete(self, recipient, escrow_id, result, proof=None) -> bool:
        from .protocol import TaskCompleteMessage
        msg = TaskCompleteMessage(escrow_id=escrow_id, result=result,
                                  completion_proof=proof).to_message(self.agent_id, recipient)
        return await self.send_message(msg)
