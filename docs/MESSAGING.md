# HYPHA Messaging Layer

Complete guide to P2P messaging between HYPHA agents.

## Overview

The messaging layer enables secure, peer-to-peer communication between autonomous agents using:
- **Hyperswarm DHT** for peer discovery
- **Direct P2P connections** for message transmission
- **NaCl signatures** for message authentication
- **Typed message protocol** for structured communication

## Architecture

```
┌──────────────┐                    ┌──────────────┐
│ Buyer Agent  │                    │Provider Agent│
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │  1. Discover via DHT              │
       │◄─────────────────────────────────►│
       │                                   │
       │  2. Task Request                  │
       │──────────────────────────────────►│
       │                                   │
       │  3. Task Response (Accept)        │
       │◄──────────────────────────────────│
       │                                   │
       │  4. Work Completion               │
       │◄──────────────────────────────────│
       │                                   │
       │  5. Payment Release               │
       │──────────────────────────────────►│
       │                                   │
```

## Message Types

### 1. Task Request
Sent from buyer to provider with task details.

```python
from hypha_sdk import Agent

buyer = Agent()

# Send task request
await buyer.messaging.send_task_request(
    recipient="provider_address",
    escrow_id="0x123...",
    task_description="Analyze blockchain data",
    amount=10.0,
    deadline=1234567890
)
```

### 2. Task Response
Provider accepts or rejects the task.

```python
# Send acceptance
await provider.messaging.send_task_response(
    recipient="buyer_address",
    escrow_id="0x123...",
    accepted=True,
    estimated_completion=1234567890,
    message_text="Starting work now"
)
```

### 3. Task Complete
Provider sends results to buyer.

```python
# Send completion
await provider.messaging.send_task_complete(
    recipient="buyer_address",
    escrow_id="0x123...",
    result={"status": "complete", "data": {...}},
    proof="hash_of_work"
)
```

### 4. Payment Notification
Notify provider of payment release.

```python
from src.messaging.protocol import PaymentNotification

payment = PaymentNotification(
    escrow_id="0x123...",
    amount=10.0,
    tx_hash="0xabc...",
    from_address="buyer_address",
    to_address="provider_address"
)
```

## Message Protocol

All messages follow a structured format:

```python
@dataclass
class Message:
    type: str              # Message type
    sender: str           # Sender agent ID
    recipient: str        # Recipient agent ID
    payload: Dict         # Message data
    timestamp: int        # Unix timestamp
    signature: str        # NaCl signature
```

## Security

### Message Signing

All messages are signed using Ed25519 (NaCl):

```python
# Messages are automatically signed
transport = MessageTransport(agent_id, private_key)
message = transport.sign_message(message)

# And verified on receipt
is_valid = transport.verify_message(message, sender_verify_key)
```

### Authentication Flow

1. Sender signs message with their private key
2. Message includes sender's agent ID
3. Recipient verifies signature using sender's public key
4. Invalid signatures are rejected

## Using the Messaging Layer

### Basic Setup

```python
from hypha_sdk import Agent
import asyncio

async def main():
    # Create agent
    agent = Agent()

    # Set up custom handlers
    async def on_task_request(escrow_id, task_description, amount, deadline, requirements=None):
        print(f"New task: {task_description} for ${amount}")
        return True  # Accept task

    agent.set_task_handler(on_task_request)

    # Start listening
    await agent.start_listening()

asyncio.run(main())
```

### Provider Pattern

```python
async def provider_workflow():
    provider = Agent()

    # Define task handler
    async def handle_task(escrow_id, task_description, amount, deadline, requirements=None):
        # Evaluate task
        if amount >= 10.0:
            print(f"Accepting task: {task_description}")
            return True
        else:
            print(f"Rejecting task: amount too low")
            return False

    # Define payment handler
    async def handle_payment(escrow_id, amount, tx_hash, from_address, to_address):
        print(f"Payment received: ${amount}")
        print(f"Transaction: {tx_hash}")

    provider.set_task_handler(handle_task)
    provider.set_payment_handler(handle_payment)

    # Announce availability
    await provider.announce("hypha-agents")

    # Listen forever
    await provider.start_listening()
```

### Buyer Pattern

```python
async def buyer_workflow():
    buyer = Agent()

    # Hire a provider
    escrow_id = await buyer.hire(
        peer="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
        amount=10.0,
        task="Analyze data"
    )

    # Define response handler
    async def handle_response(escrow_id, accepted, estimated_completion, message):
        if accepted:
            print(f"Task accepted! ETA: {estimated_completion}")
        else:
            print(f"Task rejected: {message}")

    buyer.message_handler.on_task_response(handle_response)

    # Wait for response
    await asyncio.sleep(60)
```

## Custom Message Handlers

You can override default handlers:

```python
from src.messaging.handler import MessageHandler

handler = MessageHandler()

# Custom task request handler
async def my_task_handler(escrow_id, task_description, amount, deadline, requirements=None):
    # Custom logic here
    if "urgent" in task_description.lower():
        return True  # Accept urgent tasks
    return False

# Custom payment handler
async def my_payment_handler(escrow_id, amount, tx_hash, from_address, to_address):
    # Custom logic - e.g., log to database
    db.log_payment(escrow_id, amount, tx_hash)
    print(f"Logged payment: ${amount}")

handler.on_task_request(my_task_handler)
handler.on_payment(my_payment_handler)
```

## Message Transport

### Direct Sending

```python
from src.messaging.protocol import create_message, MessageType

# Create message
message = create_message(
    msg_type=MessageType.TASK_REQUEST,
    sender=agent.agent_id,
    recipient="target_agent_id",
    escrow_id="0x123",
    task_description="Example task",
    amount=10.0,
    deadline=1234567890
)

# Send via transport
success = await agent.messaging.send_message(message)
```

### Receiving Messages

```python
# Receive next message
message = await agent.messaging.receive_messages(
    topic="hypha-agent-my_id",
    timeout=30
)

if message:
    print(f"Received {message.type} from {message.sender}")
```

## Integration with Escrow

The messaging layer integrates seamlessly with smart contracts:

```python
# 1. Create escrow on-chain
escrow_id = await buyer.hire(
    peer=provider_address,
    amount=10.0,
    task="Analysis task"
)

# 2. Task request is automatically sent via P2P
# 3. Provider receives message and decides to accept
# 4. Provider completes work and sends results
await provider.send_task_result(
    buyer_address=buyer_address,
    escrow_id=escrow_id,
    result={"analysis": "..."}
)

# 5. Buyer releases payment on-chain
await buyer.complete_task(escrow_id)

# 6. Payment notification sent via P2P
```

## Testing

### Unit Test Messages

```python
from src.messaging.protocol import TaskRequestMessage, Message

# Create test message
task_req = TaskRequestMessage(
    escrow_id="test_123",
    task_description="Test task",
    amount=5.0,
    deadline=1234567890
)

# Convert to message
message = task_req.to_message(
    sender="buyer_id",
    recipient="provider_id"
)

# Serialize
json_str = message.to_json()
bytes_data = message.to_bytes()

# Deserialize
restored = Message.from_json(json_str)
assert restored.type == message.type
```

### Integration Test

```bash
# Terminal 1: Start provider
python examples/messaging_demo.py --mode provider

# Terminal 2: Start buyer
python examples/messaging_demo.py --mode buyer
```

## Performance Considerations

### Message Size
- Keep messages under 64KB for optimal performance
- Large data should use IPFS/Arweave with hash in message

### Latency
- P2P discovery: ~1-3 seconds
- Message delivery: ~100-500ms (direct connection)
- Total round-trip: ~2-4 seconds

### Reliability
- Messages use TCP connections (reliable delivery)
- Implement retry logic for critical messages
- Use acknowledgment messages for important operations

## Best Practices

1. **Always verify signatures** before processing messages
2. **Validate message content** before acting on it
3. **Use timeouts** to prevent hanging on waiting for messages
4. **Log all messages** for debugging and audit trails
5. **Handle errors gracefully** - network issues are common
6. **Implement retry logic** for failed message sends
7. **Use unique escrow IDs** to prevent message confusion

## Troubleshooting

### Messages not being received
```bash
# Check if Hyperswarm is working
node src/messaging/receive_bridge.js test-topic

# Check if Node.js is in PATH
which node
```

### Signature verification failing
```python
# Ensure private key is consistent
agent = Agent(seed="same_seed_every_time")
```

### Peer discovery failing
```bash
# Try announcing first, then discovering
# Give 5 seconds between announce and lookup
```

## Advanced Topics

### Custom Message Types

```python
from dataclasses import dataclass
from src.messaging.protocol import Message

@dataclass
class CustomMessage:
    custom_field: str

    def to_message(self, sender: str, recipient: str) -> Message:
        return Message(
            type="custom_type",
            sender=sender,
            recipient=recipient,
            payload=asdict(self),
            timestamp=int(time.time())
        )
```

### Message Encryption

For sensitive data, add encryption layer:

```python
from nacl.public import PrivateKey, PublicKey, Box

# Encrypt payload before sending
def encrypt_message(message: str, recipient_public_key: PublicKey) -> bytes:
    box = Box(my_private_key, recipient_public_key)
    encrypted = box.encrypt(message.encode())
    return encrypted
```

## API Reference

See [API_PYTHON.md](API_PYTHON.md) for complete API documentation.

## Examples

- [messaging_demo.py](../examples/messaging_demo.py) - Complete P2P messaging demo
- [complete_workflow.py](../examples/complete_workflow.py) - Full buyer/provider workflow

## Next Steps

- Implement message persistence
- Add message queuing for offline agents
- Build message relay network for better connectivity
- Add end-to-end encryption for sensitive payloads
