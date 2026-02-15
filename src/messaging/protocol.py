"""
HYPHA Message Protocol
Defines message types and structures for P2P agent communication
"""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json
import time


class MessageType(Enum):
    """Message types for agent communication"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    TASK_COMPLETE = "task_complete"
    TASK_REJECT = "task_reject"
    PAYMENT_NOTIFICATION = "payment_notification"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class Message:
    """Base message structure"""
    type: str
    sender: str  # Agent ID or address
    recipient: str  # Agent ID or address
    payload: Dict[str, Any]
    timestamp: int
    signature: Optional[str] = None  # For message authentication

    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(**data)

    def to_bytes(self) -> bytes:
        """Serialize message to bytes for P2P transport"""
        return self.to_json().encode('utf-8')

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        """Deserialize message from bytes"""
        return cls.from_json(data.decode('utf-8'))


@dataclass
class TaskRequestMessage:
    """Task request from buyer to provider"""
    escrow_id: str
    task_description: str
    amount: float
    deadline: int
    requirements: Optional[Dict[str, Any]] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        """Convert to generic Message"""
        return Message(
            type=MessageType.TASK_REQUEST.value,
            sender=sender,
            recipient=recipient,
            payload=asdict(self),
            timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'TaskRequestMessage':
        """Extract from generic Message"""
        return cls(**message.payload)


@dataclass
class TaskResponseMessage:
    """Response from provider accepting/rejecting task"""
    escrow_id: str
    accepted: bool
    estimated_completion: Optional[int] = None  # Unix timestamp
    message: Optional[str] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        """Convert to generic Message"""
        return Message(
            type=MessageType.TASK_RESPONSE.value,
            sender=sender,
            recipient=recipient,
            payload=asdict(self),
            timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'TaskResponseMessage':
        """Extract from generic Message"""
        return cls(**message.payload)


@dataclass
class TaskCompleteMessage:
    """Task completion notification with results"""
    escrow_id: str
    result: Dict[str, Any]
    completion_proof: Optional[str] = None  # Hash or signature

    def to_message(self, sender: str, recipient: str) -> Message:
        """Convert to generic Message"""
        return Message(
            type=MessageType.TASK_COMPLETE.value,
            sender=sender,
            recipient=recipient,
            payload=asdict(self),
            timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'TaskCompleteMessage':
        """Extract from generic Message"""
        return cls(**message.payload)


@dataclass
class PaymentNotification:
    """Payment completion notification"""
    escrow_id: str
    amount: float
    tx_hash: str
    from_address: str
    to_address: str

    def to_message(self, sender: str, recipient: str) -> Message:
        """Convert to generic Message"""
        return Message(
            type=MessageType.PAYMENT_NOTIFICATION.value,
            sender=sender,
            recipient=recipient,
            payload=asdict(self),
            timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'PaymentNotification':
        """Extract from generic Message"""
        return cls(**message.payload)


@dataclass
class ErrorMessage:
    """Error notification"""
    error_code: str
    error_message: str
    context: Optional[Dict[str, Any]] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        """Convert to generic Message"""
        return Message(
            type=MessageType.ERROR.value,
            sender=sender,
            recipient=recipient,
            payload=asdict(self),
            timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'ErrorMessage':
        """Extract from generic Message"""
        return cls(**message.payload)


# Message type registry for deserialization
MESSAGE_CLASSES = {
    MessageType.TASK_REQUEST.value: TaskRequestMessage,
    MessageType.TASK_RESPONSE.value: TaskResponseMessage,
    MessageType.TASK_COMPLETE.value: TaskCompleteMessage,
    MessageType.PAYMENT_NOTIFICATION.value: PaymentNotification,
    MessageType.ERROR.value: ErrorMessage,
}


def create_message(
    msg_type: MessageType,
    sender: str,
    recipient: str,
    **kwargs
) -> Message:
    """
    Factory function to create typed messages

    Args:
        msg_type: Type of message to create
        sender: Sender agent ID
        recipient: Recipient agent ID
        **kwargs: Message-specific payload data

    Returns:
        Message instance
    """
    return Message(
        type=msg_type.value,
        sender=sender,
        recipient=recipient,
        payload=kwargs,
        timestamp=int(time.time())
    )
