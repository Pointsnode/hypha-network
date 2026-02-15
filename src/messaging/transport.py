"""
HYPHA Message Transport
Handles P2P message transmission using Hyperswarm
"""

import asyncio
import subprocess
import json
import hashlib
from typing import Optional, Callable, Dict
from .protocol import Message, MessageType
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
import os


class MessageTransport:
    """P2P message transport using Hyperswarm"""

    def __init__(self, agent_id: str, private_key: Optional[bytes] = None):
        """
        Initialize message transport

        Args:
            agent_id: Unique agent identifier
            private_key: Optional private key for message signing
        """
        self.agent_id = agent_id
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_messages = asyncio.Queue()

        # Initialize signing key for message authentication
        if private_key:
            self.signing_key = SigningKey(private_key[:32])  # NaCl uses 32 bytes
        else:
            self.signing_key = SigningKey.generate()

        self.verify_key = self.signing_key.verify_key

    def sign_message(self, message: Message) -> Message:
        """
        Sign a message for authentication

        Args:
            message: Message to sign

        Returns:
            Signed message
        """
        message_bytes = message.to_bytes()
        signed = self.signing_key.sign(message_bytes)
        message.signature = signed.signature.hex()
        return message

    def verify_message(self, message: Message, sender_verify_key: VerifyKey) -> bool:
        """
        Verify message signature

        Args:
            message: Message to verify
            sender_verify_key: Sender's verification key

        Returns:
            True if signature is valid
        """
        if not message.signature:
            return False

        try:
            # Create message copy without signature
            unsigned_message = Message(
                type=message.type,
                sender=message.sender,
                recipient=message.recipient,
                payload=message.payload,
                timestamp=message.timestamp,
                signature=None
            )

            signature_bytes = bytes.fromhex(message.signature)
            message_bytes = unsigned_message.to_bytes()

            sender_verify_key.verify(message_bytes, signature_bytes)
            return True
        except Exception:
            return False

    async def send_message(
        self,
        message: Message,
        peer_topic: Optional[str] = None
    ) -> bool:
        """
        Send message to a peer via Hyperswarm

        Args:
            message: Message to send
            peer_topic: Optional specific topic (defaults to recipient ID)

        Returns:
            True if message sent successfully
        """
        # Sign message
        signed_message = self.sign_message(message)

        # Create topic from recipient ID
        topic = peer_topic or f"hypha-agent-{message.recipient}"

        try:
            # Use bridge to send message
            # In production, this would use a persistent Hyperswarm connection
            # For now, we write to a topic-based queue

            result = subprocess.run(
                [
                    'node',
                    'src/messaging/send_bridge.js',
                    topic,
                    signed_message.to_json()
                ],
                capture_output=True,
                timeout=10,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            return result.returncode == 0

        except Exception as e:
            print(f"Failed to send message: {e}")
            return False

    async def receive_messages(
        self,
        topic: Optional[str] = None,
        timeout: int = 30
    ) -> Optional[Message]:
        """
        Receive messages from Hyperswarm

        Args:
            topic: Topic to listen on (defaults to agent's topic)
            timeout: Timeout in seconds

        Returns:
            Received message or None
        """
        listen_topic = topic or f"hypha-agent-{self.agent_id}"

        try:
            result = subprocess.run(
                [
                    'node',
                    'src/messaging/receive_bridge.js',
                    listen_topic
                ],
                capture_output=True,
                timeout=timeout,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            if result.returncode == 0 and result.stdout:
                message = Message.from_json(result.stdout)
                return message

            return None

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Failed to receive message: {e}")
            return None

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Message], None]
    ):
        """
        Register a handler for specific message type

        Args:
            message_type: Type of message to handle
            handler: Async function to handle message
        """
        self.message_handlers[message_type.value] = handler

    async def handle_message(self, message: Message):
        """
        Route message to appropriate handler

        Args:
            message: Message to handle
        """
        handler = self.message_handlers.get(message.type)

        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                print(f"Error handling message {message.type}: {e}")
        else:
            print(f"No handler registered for message type: {message.type}")

    async def start_listening(self, topic: Optional[str] = None):
        """
        Start listening for messages in background

        Args:
            topic: Topic to listen on
        """
        while True:
            message = await self.receive_messages(topic)

            if message:
                await self.handle_message(message)

            # Small delay to prevent tight loop
            await asyncio.sleep(0.1)

    async def send_task_request(
        self,
        recipient: str,
        escrow_id: str,
        task_description: str,
        amount: float,
        deadline: int
    ) -> bool:
        """
        Send task request to provider

        Args:
            recipient: Provider agent ID
            escrow_id: Escrow contract ID
            task_description: Task details
            amount: Payment amount
            deadline: Task deadline (Unix timestamp)

        Returns:
            True if sent successfully
        """
        from .protocol import TaskRequestMessage

        task_msg = TaskRequestMessage(
            escrow_id=escrow_id,
            task_description=task_description,
            amount=amount,
            deadline=deadline
        )

        message = task_msg.to_message(
            sender=self.agent_id,
            recipient=recipient
        )

        return await self.send_message(message)

    async def send_task_response(
        self,
        recipient: str,
        escrow_id: str,
        accepted: bool,
        estimated_completion: Optional[int] = None,
        message_text: Optional[str] = None
    ) -> bool:
        """
        Send task acceptance/rejection

        Args:
            recipient: Buyer agent ID
            escrow_id: Escrow contract ID
            accepted: Whether task is accepted
            estimated_completion: Estimated completion time
            message_text: Optional message to buyer

        Returns:
            True if sent successfully
        """
        from .protocol import TaskResponseMessage

        response_msg = TaskResponseMessage(
            escrow_id=escrow_id,
            accepted=accepted,
            estimated_completion=estimated_completion,
            message=message_text
        )

        message = response_msg.to_message(
            sender=self.agent_id,
            recipient=recipient
        )

        return await self.send_message(message)

    async def send_task_complete(
        self,
        recipient: str,
        escrow_id: str,
        result: Dict,
        proof: Optional[str] = None
    ) -> bool:
        """
        Send task completion notification

        Args:
            recipient: Buyer agent ID
            escrow_id: Escrow contract ID
            result: Task results
            proof: Optional completion proof

        Returns:
            True if sent successfully
        """
        from .protocol import TaskCompleteMessage

        complete_msg = TaskCompleteMessage(
            escrow_id=escrow_id,
            result=result,
            completion_proof=proof
        )

        message = complete_msg.to_message(
            sender=self.agent_id,
            recipient=recipient
        )

        return await self.send_message(message)
