"""
HYPHA Message Protocol (Pure Python)
Ported from src/messaging/protocol.py
"""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json
import time


class MessageType(Enum):
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
    type: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    timestamp: int
    signature: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        return cls(**json.loads(json_str))

    def to_bytes(self) -> bytes:
        return self.to_json().encode('utf-8')

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        return cls.from_json(data.decode('utf-8'))


@dataclass
class TaskRequestMessage:
    escrow_id: str
    task_description: str
    amount: float
    deadline: int
    requirements: Optional[Dict[str, Any]] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        return Message(
            type=MessageType.TASK_REQUEST.value,
            sender=sender, recipient=recipient,
            payload=asdict(self), timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'TaskRequestMessage':
        return cls(**message.payload)


@dataclass
class TaskResponseMessage:
    escrow_id: str
    accepted: bool
    estimated_completion: Optional[int] = None
    message: Optional[str] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        return Message(
            type=MessageType.TASK_RESPONSE.value,
            sender=sender, recipient=recipient,
            payload=asdict(self), timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'TaskResponseMessage':
        return cls(**message.payload)


@dataclass
class TaskCompleteMessage:
    escrow_id: str
    result: Dict[str, Any]
    completion_proof: Optional[str] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        return Message(
            type=MessageType.TASK_COMPLETE.value,
            sender=sender, recipient=recipient,
            payload=asdict(self), timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'TaskCompleteMessage':
        return cls(**message.payload)


@dataclass
class PaymentNotification:
    escrow_id: str
    amount: float
    tx_hash: str
    from_address: str
    to_address: str

    def to_message(self, sender: str, recipient: str) -> Message:
        return Message(
            type=MessageType.PAYMENT_NOTIFICATION.value,
            sender=sender, recipient=recipient,
            payload=asdict(self), timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'PaymentNotification':
        return cls(**message.payload)


@dataclass
class ErrorMessage:
    error_code: str
    error_message: str
    context: Optional[Dict[str, Any]] = None

    def to_message(self, sender: str, recipient: str) -> Message:
        return Message(
            type=MessageType.ERROR.value,
            sender=sender, recipient=recipient,
            payload=asdict(self), timestamp=int(time.time())
        )

    @classmethod
    def from_message(cls, message: Message) -> 'ErrorMessage':
        return cls(**message.payload)


MESSAGE_CLASSES = {
    MessageType.TASK_REQUEST.value: TaskRequestMessage,
    MessageType.TASK_RESPONSE.value: TaskResponseMessage,
    MessageType.TASK_COMPLETE.value: TaskCompleteMessage,
    MessageType.PAYMENT_NOTIFICATION.value: PaymentNotification,
    MessageType.ERROR.value: ErrorMessage,
}


def create_message(msg_type: MessageType, sender: str, recipient: str, **kwargs) -> Message:
    return Message(
        type=msg_type.value, sender=sender, recipient=recipient,
        payload=kwargs, timestamp=int(time.time())
    )
