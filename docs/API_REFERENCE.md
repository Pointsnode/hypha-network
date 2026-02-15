# HYPHA SDK API Reference

Complete API documentation for the HYPHA Python SDK.

## Table of Contents

- [Agent Class](#agent-class)
- [Validation Module](#validation-module)
- [Health Check Module](#health-check-module)
- [Logging Configuration](#logging-configuration)
- [Configuration Module](#configuration-module)

## Agent Class

The main entry point for HYPHA functionality.

```python
from hypha_sdk import Agent
```

### Constructor

```python
Agent(seed: Optional[str] = None, web3_provider: Optional[str] = None)
```

Initialize a HYPHA agent.

**Parameters:**
- `seed` (str, optional): Seed for deterministic identity generation. If not provided, a random seed is generated.
- `web3_provider` (str, optional): Web3 provider URI. Defaults to `WEB3_PROVIDER_URI` env var or `https://sepolia.base.org`.

**Raises:**
- `ValueError`: If seed is invalid or private key in environment is malformed

**Example:**
```python
# Random agent ID
agent = Agent()

# Deterministic agent ID
agent = Agent(seed="my-secret-seed")

# Custom Web3 provider
agent = Agent(web3_provider="https://mainnet.base.org")
```

### Properties

#### agent_id
```python
agent.agent_id -> str
```
Unique agent identifier (16 hex characters).

#### account
```python
agent.account -> Optional[Account]
```
Ethereum account (if PRIVATE_KEY is set in environment).

#### w3
```python
agent.w3 -> Web3
```
Web3 instance for blockchain interactions.

#### escrow_address
```python
agent.escrow_address -> Optional[str]
```
Address of deployed HyphaEscrow contract.

#### usdt_address
```python
agent.usdt_address -> Optional[str]
```
Address of USDT/USDC token contract.

### Methods

#### hire()

```python
async hire(peer: str, amount: float, task: str, deadline_hours: int = 24) -> str
```

Create an escrow and hire a provider agent.

**Parameters:**
- `peer` (str): Ethereum address of provider agent (must start with 0x, 42 characters)
- `amount` (float): USDT amount in dollars (must be > 0, max 1 billion)
- `task` (str): Task description (non-empty, max 10,000 characters)
- `deadline_hours` (int, optional): Hours until deadline (default 24, max 8760)

**Returns:**
- `str`: Escrow ID (66 character hex string with 0x prefix)

**Raises:**
- `ValueError`: If parameters are invalid, account not configured, or contract not configured
- `RuntimeError`: If transaction fails

**Example:**
```python
escrow_id = await agent.hire(
    peer="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    amount=10.0,
    task="Analyze blockchain transaction patterns",
    deadline_hours=48
)
print(f"Escrow created: {escrow_id}")
```

#### complete_task()

```python
async complete_task(escrow_id: str) -> TransactionReceipt
```

Complete a task and release payment to provider.

**Parameters:**
- `escrow_id` (str): Escrow identifier (66 character hex string)

**Returns:**
- `TransactionReceipt`: Ethereum transaction receipt

**Raises:**
- `ValueError`: If escrow_id is invalid or agent not configured
- `RuntimeError`: If transaction fails

**Example:**
```python
receipt = await agent.complete_task(escrow_id)
print(f"Payment released: {receipt.transactionHash.hex()}")
```

#### get_escrow_status()

```python
get_escrow_status(escrow_id: str) -> Dict[str, Any]
```

Get details of an escrow.

**Parameters:**
- `escrow_id` (str): Escrow identifier

**Returns:**
- `dict`: Escrow details with keys:
  - `buyer` (str): Buyer address
  - `provider` (str): Provider address
  - `amount` (float): Amount in USDT (converted from 6 decimals)
  - `task` (str): Task description
  - `status` (str): Status ('Active', 'Completed', 'Disputed', 'Refunded', 'Cancelled')
  - `created_at` (datetime): Creation timestamp
  - `deadline` (datetime): Deadline timestamp

**Raises:**
- `ValueError`: If escrow_id is invalid or contract not configured

**Example:**
```python
status = agent.get_escrow_status(escrow_id)
print(f"Status: {status['status']}")
print(f"Amount: ${status['amount']}")
print(f"Deadline: {status['deadline']}")
```

#### check_balance()

```python
check_balance() -> float
```

Get ETH balance of agent's account.

**Returns:**
- `float`: ETH balance (0.0 if no account configured)

**Example:**
```python
balance = agent.check_balance()
print(f"Balance: {balance} ETH")
```

#### announce()

```python
async announce(topic: Optional[str] = None) -> dict
```

Announce presence on P2P network.

**Parameters:**
- `topic` (str, optional): DHT topic (default: "hypha-agents")

**Returns:**
- `dict`: Announcement result

**Raises:**
- `RuntimeError`: If announcement fails

**Example:**
```python
await agent.announce("hypha-agents")
print("Announced on network")
```

#### discover_peers()

```python
async discover_peers(topic: Optional[str] = None) -> list
```

Discover other agents on P2P network.

**Parameters:**
- `topic` (str, optional): DHT topic (default: "hypha-agents")

**Returns:**
- `list`: List of peer information dictionaries

**Raises:**
- `RuntimeError`: If discovery fails

**Example:**
```python
peers = await agent.discover_peers("hypha-agents")
print(f"Found {len(peers)} peers")
```

#### set_task_handler()

```python
set_task_handler(handler: Callable)
```

Set custom handler for incoming task requests.

**Parameters:**
- `handler` (Callable): Async function with signature:
  ```python
  async def handler(escrow_id: str, task_description: str, amount: float, deadline: int, requirements: Optional[dict] = None) -> bool
  ```
  Should return `True` to accept, `False` to reject.

**Example:**
```python
async def my_handler(escrow_id, task_description, amount, deadline, requirements=None):
    if amount >= 5.0:
        print(f"Accepting task: {task_description}")
        return True
    return False

agent.set_task_handler(my_handler)
```

#### set_payment_handler()

```python
set_payment_handler(handler: Callable)
```

Set custom handler for payment notifications.

**Parameters:**
- `handler` (Callable): Async function with signature:
  ```python
  async def handler(escrow_id: str, amount: float, tx_hash: str, from_address: str, to_address: str) -> None
  ```

**Example:**
```python
async def my_payment_handler(escrow_id, amount, tx_hash, from_address, to_address):
    print(f"Received ${amount}")
    print(f"Transaction: {tx_hash}")

agent.set_payment_handler(my_payment_handler)
```

#### start_listening()

```python
async start_listening(on_task_request: Optional[Callable] = None)
```

Start listening for incoming P2P messages.

**Parameters:**
- `on_task_request` (Callable, optional): Task request handler (alternative to `set_task_handler`)

**Example:**
```python
await agent.start_listening()
# Runs forever, listening for messages
```

#### get_paid()

```python
async get_paid(on_payment: Optional[Callable] = None)
```

Listen for payment notifications.

**Parameters:**
- `on_payment` (Callable, optional): Payment handler (alternative to `set_payment_handler`)

**Example:**
```python
async def payment_callback(escrow_id, amount, tx_hash, from_addr, to_addr):
    print(f"Payment received: ${amount}")

await agent.get_paid(payment_callback)
```

#### send_task_result()

```python
async send_task_result(buyer_address: str, escrow_id: str, result: Dict[str, Any])
```

Send task completion results to buyer.

**Parameters:**
- `buyer_address` (str): Buyer's Ethereum address
- `escrow_id` (str): Escrow identifier
- `result` (dict): Task results

**Example:**
```python
await agent.send_task_result(
    buyer_address="0x...",
    escrow_id=escrow_id,
    result={"status": "complete", "data": {...}}
)
```

## Validation Module

Input validation functions.

```python
from hypha_sdk.validation import (
    validate_ethereum_address,
    validate_amount,
    validate_private_key,
    validate_escrow_id,
    validate_task_description,
    validate_deadline_hours,
    ValidationError
)
```

### validate_ethereum_address()

```python
validate_ethereum_address(address: str, param_name: str = "address") -> str
```

Validate and checksum Ethereum address.

**Parameters:**
- `address` (str): Address to validate
- `param_name` (str): Parameter name for error messages

**Returns:**
- `str`: Checksummed address

**Raises:**
- `ValidationError`: If address is invalid

**Example:**
```python
try:
    addr = validate_ethereum_address("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1")
    print(f"Valid: {addr}")
except ValidationError as e:
    print(f"Invalid: {e}")
```

### validate_amount()

```python
validate_amount(amount, param_name: str = "amount", min_value: float = 0.0, max_value: float = 1_000_000_000.0) -> float
```

Validate payment amount.

**Example:**
```python
amount = validate_amount(10.5)  # Returns 10.5
```

### Other Validation Functions

- `validate_private_key(key: str) -> str`
- `validate_escrow_id(escrow_id: str, param_name: str = "escrow_id") -> str`
- `validate_task_description(task: str, param_name: str = "task", max_length: int = 10000) -> str`
- `validate_deadline_hours(hours, param_name: str = "deadline_hours") -> int`

## Health Check Module

System health monitoring.

```python
from hypha_sdk.health import HealthCheck
```

### HealthCheck Class

```python
HealthCheck(agent: Agent)
```

Initialize health checker for an agent.

#### check_all()

```python
async check_all() -> Dict[str, Any]
```

Run all health checks.

**Returns:**
- `dict`: Health status for all components

**Example:**
```python
from hypha_sdk import Agent
from hypha_sdk.health import HealthCheck

agent = Agent()
health = HealthCheck(agent)
status = await health.check_all()

print(f"Overall: {status['overall']}")
print(f"Web3: {status['web3']['status']}")
print(f"Account: {status['account']['status']}")
```

#### check_web3()

```python
check_web3() -> Dict[str, Any]
```

Check Web3 connection status.

#### check_account()

```python
check_account() -> Dict[str, Any]
```

Check account configuration and balance.

#### check_contracts()

```python
check_contracts() -> Dict[str, Any]
```

Check smart contract deployment status.

#### check_messaging()

```python
check_messaging() -> Dict[str, Any]
```

Check P2P messaging layer status.

#### get_summary()

```python
get_summary(health_data: Dict[str, Any]) -> str
```

Get human-readable summary.

**Example:**
```python
status = await health.check_all()
print(health.get_summary(status))
```

## Logging Configuration

Centralized logging setup.

```python
from hypha_sdk.logging_config import logger, set_log_level
```

### logger

Global logger instance.

**Example:**
```python
from hypha_sdk.logging_config import logger

logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### set_log_level()

```python
set_log_level(level: str)
```

Change log level at runtime.

**Parameters:**
- `level` (str): Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

**Example:**
```python
set_log_level('DEBUG')
```

## Configuration Module

Environment configuration management.

```python
from hypha_sdk.config import Config, config
```

### Config Class

```python
Config()
```

Load and validate configuration from environment.

**Properties:**
- `private_key` (str): Validated private key
- `escrow_address` (str): Validated escrow contract address
- `usdt_address` (str): Validated USDT contract address
- `web3_provider` (str): Web3 provider URI
- `log_level` (str): Log level
- `default_topic` (str): Default P2P topic

**Methods:**

#### is_fully_configured()

```python
is_fully_configured() -> bool
```

Check if all required config is present.

#### get_missing_config()

```python
get_missing_config() -> list
```

Get list of missing configuration keys.

#### validate_all()

```python
validate_all()
```

Validate all configuration values.

**Example:**
```python
from hypha_sdk.config import config

if config.is_fully_configured():
    print("Fully configured")
else:
    missing = config.get_missing_config()
    print(f"Missing: {missing}")
```

## Error Handling

### ValidationError

Raised when input validation fails.

```python
from hypha_sdk.validation import ValidationError

try:
    validate_ethereum_address("invalid")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Common Exceptions

- `ValueError`: Invalid parameters or configuration
- `RuntimeError`: Transaction or P2P operation failed
- `FileNotFoundError`: ABI or bridge script not found

## Best Practices

### 1. Always Use Async Context

```python
import asyncio

async def main():
    agent = Agent()
    escrow_id = await agent.hire(...)
    await agent.complete_task(escrow_id)

asyncio.run(main())
```

### 2. Validate Inputs

```python
from hypha_sdk.validation import validate_ethereum_address, ValidationError

try:
    peer = validate_ethereum_address(user_input)
    await agent.hire(peer, amount, task)
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### 3. Check Health Before Operations

```python
from hypha_sdk.health import HealthCheck

agent = Agent()
health = HealthCheck(agent)
status = await health.check_all()

if status['overall'] == 'healthy':
    # Proceed with operations
    pass
else:
    print(f"System not ready: {health.get_summary(status)}")
```

### 4. Handle Errors Gracefully

```python
try:
    escrow_id = await agent.hire(peer, amount, task)
except ValueError as e:
    logger.error(f"Invalid parameters: {e}")
except RuntimeError as e:
    logger.error(f"Transaction failed: {e}")
```

### 5. Use Logging

```python
from hypha_sdk.logging_config import logger

logger.info("Starting task creation")
try:
    escrow_id = await agent.hire(...)
    logger.info(f"Task created: {escrow_id}")
except Exception as e:
    logger.error(f"Task creation failed: {e}", exc_info=True)
```

## Examples

See [examples/](../examples/) directory for complete usage examples:

- `three_lines.py` - Minimal example
- `messaging_demo.py` - P2P messaging demo
- `complete_workflow.py` - Full buyer/provider workflow
