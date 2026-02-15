"""
HYPHA Message Handler
Default handlers for common message types
"""

import asyncio
from typing import Callable, Dict, Any, Optional
from .protocol import (
    Message,
    MessageType,
    TaskRequestMessage,
    TaskResponseMessage,
    TaskCompleteMessage,
    PaymentNotification
)


class MessageHandler:
    """Handles incoming messages with user-defined callbacks"""

    def __init__(self):
        self.task_request_callback: Optional[Callable] = None
        self.task_response_callback: Optional[Callable] = None
        self.task_complete_callback: Optional[Callable] = None
        self.payment_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None

        # Store active tasks
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def on_task_request(self, callback: Callable):
        """
        Register callback for task requests

        Callback signature: async def callback(escrow_id, task_description, amount, deadline) -> bool
        Returns True to accept, False to reject
        """
        self.task_request_callback = callback

    def on_task_response(self, callback: Callable):
        """
        Register callback for task responses

        Callback signature: async def callback(escrow_id, accepted, estimated_completion, message)
        """
        self.task_response_callback = callback

    def on_task_complete(self, callback: Callable):
        """
        Register callback for task completion

        Callback signature: async def callback(escrow_id, result, proof)
        """
        self.task_complete_callback = callback

    def on_payment(self, callback: Callable):
        """
        Register callback for payment notifications

        Callback signature: async def callback(escrow_id, amount, tx_hash, from_addr, to_addr)
        """
        self.payment_callback = callback

    def on_error(self, callback: Callable):
        """
        Register callback for errors

        Callback signature: async def callback(error_code, error_message, context)
        """
        self.error_callback = callback

    async def handle_task_request(self, message: Message) -> Optional[bool]:
        """
        Handle incoming task request

        Args:
            message: Task request message

        Returns:
            True if accepted, False if rejected, None if no handler
        """
        task_req = TaskRequestMessage.from_message(message)

        # Store task info
        self.active_tasks[task_req.escrow_id] = {
            'sender': message.sender,
            'description': task_req.task_description,
            'amount': task_req.amount,
            'deadline': task_req.deadline,
            'status': 'pending'
        }

        if self.task_request_callback:
            try:
                accepted = await self.task_request_callback(
                    escrow_id=task_req.escrow_id,
                    task_description=task_req.task_description,
                    amount=task_req.amount,
                    deadline=task_req.deadline,
                    requirements=task_req.requirements
                )

                if accepted:
                    self.active_tasks[task_req.escrow_id]['status'] = 'accepted'
                else:
                    self.active_tasks[task_req.escrow_id]['status'] = 'rejected'

                return accepted

            except Exception as e:
                print(f"Error in task request callback: {e}")
                return False

        return None

    async def handle_task_response(self, message: Message):
        """
        Handle task acceptance/rejection

        Args:
            message: Task response message
        """
        task_resp = TaskResponseMessage.from_message(message)

        # Update task status
        if task_resp.escrow_id in self.active_tasks:
            self.active_tasks[task_resp.escrow_id]['status'] = (
                'accepted' if task_resp.accepted else 'rejected'
            )
            if task_resp.estimated_completion:
                self.active_tasks[task_resp.escrow_id]['estimated_completion'] = (
                    task_resp.estimated_completion
                )

        if self.task_response_callback:
            try:
                await self.task_response_callback(
                    escrow_id=task_resp.escrow_id,
                    accepted=task_resp.accepted,
                    estimated_completion=task_resp.estimated_completion,
                    message=task_resp.message
                )
            except Exception as e:
                print(f"Error in task response callback: {e}")

    async def handle_task_complete(self, message: Message):
        """
        Handle task completion

        Args:
            message: Task completion message
        """
        task_complete = TaskCompleteMessage.from_message(message)

        # Update task status
        if task_complete.escrow_id in self.active_tasks:
            self.active_tasks[task_complete.escrow_id]['status'] = 'completed'
            self.active_tasks[task_complete.escrow_id]['result'] = task_complete.result

        if self.task_complete_callback:
            try:
                await self.task_complete_callback(
                    escrow_id=task_complete.escrow_id,
                    result=task_complete.result,
                    proof=task_complete.completion_proof
                )
            except Exception as e:
                print(f"Error in task complete callback: {e}")

    async def handle_payment(self, message: Message):
        """
        Handle payment notification

        Args:
            message: Payment notification message
        """
        payment = PaymentNotification.from_message(message)

        # Update task status
        if payment.escrow_id in self.active_tasks:
            self.active_tasks[payment.escrow_id]['status'] = 'paid'
            self.active_tasks[payment.escrow_id]['tx_hash'] = payment.tx_hash

        if self.payment_callback:
            try:
                await self.payment_callback(
                    escrow_id=payment.escrow_id,
                    amount=payment.amount,
                    tx_hash=payment.tx_hash,
                    from_address=payment.from_address,
                    to_address=payment.to_address
                )
            except Exception as e:
                print(f"Error in payment callback: {e}")

    def get_task_status(self, escrow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a task

        Args:
            escrow_id: Escrow identifier

        Returns:
            Task information or None
        """
        return self.active_tasks.get(escrow_id)

    def list_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active tasks"""
        return {
            eid: info for eid, info in self.active_tasks.items()
            if info['status'] in ['pending', 'accepted']
        }


# Default handler implementations

async def default_task_request_handler(
    escrow_id: str,
    task_description: str,
    amount: float,
    deadline: int,
    requirements: Optional[Dict] = None
) -> bool:
    """
    Default task request handler - auto-accepts all tasks

    Override this in production!
    """
    print(f"\n📩 Task Request Received:")
    print(f"  Escrow ID: {escrow_id}")
    print(f"  Task: {task_description}")
    print(f"  Amount: ${amount}")
    print(f"  Deadline: {deadline}")

    # Auto-accept (override in production)
    return True


async def default_task_response_handler(
    escrow_id: str,
    accepted: bool,
    estimated_completion: Optional[int],
    message: Optional[str]
):
    """Default task response handler"""
    print(f"\n📬 Task Response:")
    print(f"  Escrow ID: {escrow_id}")
    print(f"  Accepted: {accepted}")
    if estimated_completion:
        print(f"  ETA: {estimated_completion}")
    if message:
        print(f"  Message: {message}")


async def default_task_complete_handler(
    escrow_id: str,
    result: Dict[str, Any],
    proof: Optional[str]
):
    """Default task completion handler"""
    print(f"\n✅ Task Completed:")
    print(f"  Escrow ID: {escrow_id}")
    print(f"  Result: {result}")
    if proof:
        print(f"  Proof: {proof}")


async def default_payment_handler(
    escrow_id: str,
    amount: float,
    tx_hash: str,
    from_address: str,
    to_address: str
):
    """Default payment notification handler"""
    print(f"\n💰 Payment Received:")
    print(f"  Escrow ID: {escrow_id}")
    print(f"  Amount: ${amount}")
    print(f"  Tx Hash: {tx_hash}")
    print(f"  From: {from_address}")
    print(f"  To: {to_address}")
