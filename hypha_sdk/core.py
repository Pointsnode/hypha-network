"""
HYPHA Unified SDK
Three-line API for autonomous agent coordination
"""

import os
import json
import hashlib
import subprocess
import asyncio
import sys
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from web3 import Web3
from web3.contract import Contract
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import messaging components
from src.messaging.transport import MessageTransport
from src.messaging.handler import MessageHandler
from src.messaging.protocol import MessageType

# Import validation and logging
from .validation import (
    validate_ethereum_address,
    validate_amount,
    validate_private_key,
    validate_escrow_id,
    validate_task_description,
    validate_deadline_hours,
    validate_seed,
    ValidationError
)
from .logging_config import logger

# Load environment variables
load_dotenv()


def _get_bridge_path(bridge_file: str) -> str:
    """Get absolute path to Node.js bridge script"""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    # Try development structure (hypha-project/hypha_sdk/)
    dev_path = os.path.join(os.path.dirname(current_dir), 'src', bridge_file)
    if os.path.exists(dev_path):
        return dev_path

    # Try installed package structure
    pkg_path = os.path.join(current_dir, '..', 'src', bridge_file)
    if os.path.exists(pkg_path):
        return os.path.abspath(pkg_path)

    raise FileNotFoundError(f"Bridge script not found: {bridge_file}")


def _load_contract_abi(abi_name: str) -> list:
    """
    Load ABI from JSON file

    Args:
        abi_name: Name of ABI file (without .json extension)

    Returns:
        ABI as list of dictionaries
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    abi_path = os.path.join(current_dir, 'abis', f'{abi_name}.json')

    if not os.path.exists(abi_path):
        raise FileNotFoundError(f"ABI file not found: {abi_path}")

    with open(abi_path, 'r') as f:
        return json.load(f)


class Agent:
    """Unified HYPHA agent with P2P + Payments"""

    def __init__(self, seed: Optional[str] = None, web3_provider: Optional[str] = None):
        """
        Initialize HYPHA agent

        Args:
            seed: Optional seed for deterministic identity
            web3_provider: Optional Web3 provider URI (defaults to env var)
        """
        # Validate seed if provided
        if seed is not None:
            try:
                seed = validate_seed(seed)
            except ValidationError as e:
                logger.error(f"Invalid seed: {e}")
                raise ValueError(str(e)) from e

        self.seed = seed or self._generate_seed()
        self.keypair = self._derive_keypair(self.seed)
        self.agent_id = self.keypair['public'][:16]

        logger.debug(f"Initialized agent with ID: {self.agent_id}")

        # Web3 setup
        provider_uri = web3_provider or os.getenv('WEB3_PROVIDER_URI', 'https://sepolia.base.org')
        self.w3 = Web3(Web3.HTTPProvider(provider_uri))

        # Load private key and create account
        private_key = os.getenv('PRIVATE_KEY')
        if private_key:
            try:
                private_key = validate_private_key(private_key)
                self.account = self.w3.eth.account.from_key(private_key)
                logger.info(f"Account configured: {self.account.address}")
            except ValidationError as e:
                logger.error(f"Invalid PRIVATE_KEY in environment: {e}")
                raise ValueError(f"Invalid PRIVATE_KEY: {e}") from e
        else:
            self.account = None
            logger.warning("No PRIVATE_KEY set - agent cannot create escrows or sign transactions")

        # Load contract addresses
        self.escrow_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
        self.usdt_address = os.getenv('USDT_CONTRACT_ADDRESS')

        # Load contract ABIs
        self.escrow_contract = self._load_escrow_contract() if self.escrow_address else None

        self._connected = False
        self._topic = "hypha-agents"

        # Initialize messaging
        private_key_bytes = bytes.fromhex(private_key.replace('0x', '')) if private_key else None
        self.messaging = MessageTransport(self.agent_id, private_key_bytes)
        self.message_handler = MessageHandler()

        # Setup default message handlers
        self._setup_message_handlers()

    def _generate_seed(self) -> str:
        """Generate cryptographic seed"""
        return hashlib.sha256(os.urandom(32)).hexdigest()

    def _derive_keypair(self, seed: str) -> dict:
        """Deterministic key derivation from seed"""
        secret = hashlib.pbkdf2_hmac(
            'sha256', seed.encode(), b'hypha-identity',
            100000, dklen=32
        )
        public = hashlib.sha256(secret + b'public').digest()
        return {'public': public.hex(), 'secret': secret.hex()}

    def _load_escrow_contract(self) -> Optional[Contract]:
        """Load HyphaEscrow contract with ABI from external file"""
        if not self.escrow_address:
            return None

        try:
            escrow_abi = _load_contract_abi('escrow_abi')
            return self.w3.eth.contract(
                address=Web3.to_checksum_address(self.escrow_address),
                abi=escrow_abi
            )
        except FileNotFoundError as e:
            logger.error(f"Failed to load escrow ABI: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create escrow contract: {e}")
            raise

    async def hire(
        self,
        peer: str,
        amount: float,
        task: str,
        deadline_hours: int = 24
    ) -> str:
        """
        God function: discovery + messaging + payments

        Args:
            peer: Target agent address or ID
            amount: USDT amount (in dollars, e.g., 10.0 for $10)
            task: Task description
            deadline_hours: Hours until task deadline (default 24)

        Returns:
            Escrow ID (hex string)
        """
        if not self.account:
            logger.error("Cannot hire: No account configured")
            raise ValueError("No account configured. Set PRIVATE_KEY in .env")

        if not self.escrow_contract:
            logger.error("Cannot hire: No escrow contract configured")
            raise ValueError("No escrow contract configured. Set ESCROW_CONTRACT_ADDRESS in .env")

        # Validate all inputs
        try:
            peer_address = validate_ethereum_address(peer, "peer")
            validated_amount = validate_amount(amount, "amount")
            validated_task = validate_task_description(task, "task")
            validated_hours = validate_deadline_hours(deadline_hours, "deadline_hours")
        except ValidationError as e:
            logger.error(f"Validation failed in hire(): {e}")
            raise ValueError(str(e)) from e

        logger.info(f"Creating escrow for {validated_amount} USDT with {peer_address}")

        # Convert amount to USDT units (6 decimals)
        amount_units = int(validated_amount * 10**6)

        # Calculate deadline timestamp
        deadline = int((datetime.now() + timedelta(hours=validated_hours)).timestamp())

        # Create escrow on-chain
        escrow_id = await self._create_escrow(
            peer_address,
            amount_units,
            validated_task,
            deadline
        )

        logger.info(f"Escrow created: {escrow_id}")

        # Send P2P message to notify peer
        try:
            await self._send_message(peer_address, {
                "type": "task_request",
                "escrow_id": escrow_id,
                "task": validated_task,
                "amount": validated_amount,
                "deadline": deadline
            })
            logger.debug(f"Task request sent to {peer_address}")
        except Exception as e:
            logger.warning(f"Failed to send P2P message: {e}")

        return escrow_id

    async def complete_task(self, escrow_id: str):
        """
        Complete a task and release payment to provider

        Args:
            escrow_id: The escrow identifier (hex string)
        """
        if not self.account or not self.escrow_contract:
            logger.error("Cannot complete task: Agent not properly configured")
            raise ValueError("Agent not properly configured")

        # Validate escrow ID
        try:
            validated_id = validate_escrow_id(escrow_id, "escrow_id")
        except ValidationError as e:
            logger.error(f"Invalid escrow_id: {e}")
            raise ValueError(str(e)) from e

        logger.info(f"Completing escrow: {validated_id}")

        escrow_bytes = bytes.fromhex(validated_id.replace('0x', ''))

        # Build transaction
        tx = self.escrow_contract.functions.completeEscrow(escrow_bytes).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price
        })

        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        logger.info(f"Task completed successfully: {validated_id}")

        return receipt

    def get_escrow_status(self, escrow_id: str) -> Dict[str, Any]:
        """
        Get escrow details

        Args:
            escrow_id: The escrow identifier (hex string)

        Returns:
            Escrow details dictionary
        """
        if not self.escrow_contract:
            logger.error("Cannot get escrow status: No escrow contract configured")
            raise ValueError("No escrow contract configured")

        # Validate escrow ID
        try:
            validated_id = validate_escrow_id(escrow_id, "escrow_id")
        except ValidationError as e:
            logger.error(f"Invalid escrow_id: {e}")
            raise ValueError(str(e)) from e

        escrow_bytes = bytes.fromhex(validated_id.replace('0x', ''))

        result = self.escrow_contract.functions.getEscrow(escrow_bytes).call()

        status_names = ['Active', 'Completed', 'Disputed', 'Refunded', 'Cancelled']

        return {
            'buyer': result[0],
            'provider': result[1],
            'amount': result[2] / 10**6,  # Convert to dollars
            'task': result[3],
            'status': status_names[result[4]],
            'created_at': datetime.fromtimestamp(result[5]),
            'deadline': datetime.fromtimestamp(result[6])
        }

    def check_balance(self) -> float:
        """Get ETH balance in account"""
        if not self.account:
            return 0.0

        balance_wei = self.w3.eth.get_balance(self.account.address)
        return float(self.w3.from_wei(balance_wei, 'ether'))

    async def announce(self, topic: Optional[str] = None):
        """
        Announce presence on P2P network

        Args:
            topic: DHT topic to announce on (default: "hypha-agents")
        """
        topic = topic or self._topic

        logger.info(f"Announcing on P2P network: {topic}")

        try:
            bridge_path = _get_bridge_path('discovery/bridge.js')
            result = subprocess.run(
                ['node', bridge_path, 'announce', topic],
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode == 0:
                self._connected = True
                logger.info(f"Successfully announced on {topic}")
                return json.loads(result.stdout)
            else:
                logger.error(f"Announce failed: {result.stderr}")
                raise RuntimeError(f"Announce failed: {result.stderr}")

        except Exception as e:
            logger.error(f"P2P announce failed: {e}", exc_info=True)
            raise RuntimeError(f"P2P announce failed: {e}")

    async def discover_peers(self, topic: Optional[str] = None) -> list:
        """
        Discover peers on P2P network

        Args:
            topic: DHT topic to search (default: "hypha-agents")

        Returns:
            List of peer information dictionaries
        """
        topic = topic or self._topic

        logger.info(f"Discovering peers on topic: {topic}")

        try:
            bridge_path = _get_bridge_path('discovery/bridge.js')
            result = subprocess.run(
                ['node', bridge_path, 'lookup', topic],
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode == 0:
                peers = json.loads(result.stdout)
                logger.info(f"Discovered {len(peers)} peers")
                return peers
            else:
                logger.warning(f"Peer discovery returned no results")
                return []

        except Exception as e:
            logger.error(f"Peer discovery failed: {e}", exc_info=True)
            raise RuntimeError(f"Peer discovery failed: {e}")

    async def _create_escrow(
        self,
        provider: str,
        amount: int,
        task: str,
        deadline: int
    ) -> str:
        """Create USDT escrow on-chain"""

        # Build transaction
        tx = self.escrow_contract.functions.createEscrow(
            provider,
            amount,
            task,
            deadline
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price
        })

        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        # Parse EscrowCreated event to get actual escrow ID
        escrow_created = self.escrow_contract.events.EscrowCreated()
        logs = escrow_created.process_receipt(receipt)

        if not logs:
            raise RuntimeError("EscrowCreated event not found in transaction receipt")

        escrow_id = logs[0]['args']['escrowId'].hex()
        return escrow_id

    def _setup_message_handlers(self):
        """Setup default message handlers"""
        from src.messaging.handler import (
            default_task_request_handler,
            default_task_response_handler,
            default_task_complete_handler,
            default_payment_handler
        )

        # Register default handlers
        self.message_handler.on_task_request(default_task_request_handler)
        self.message_handler.on_task_response(default_task_response_handler)
        self.message_handler.on_task_complete(default_task_complete_handler)
        self.message_handler.on_payment(default_payment_handler)

        # Register handlers with transport
        self.messaging.register_handler(
            MessageType.TASK_REQUEST,
            self.message_handler.handle_task_request
        )
        self.messaging.register_handler(
            MessageType.TASK_RESPONSE,
            self.message_handler.handle_task_response
        )
        self.messaging.register_handler(
            MessageType.TASK_COMPLETE,
            self.message_handler.handle_task_complete
        )
        self.messaging.register_handler(
            MessageType.PAYMENT_NOTIFICATION,
            self.message_handler.handle_payment
        )

    async def _send_message(self, peer: str, message: dict):
        """Send P2P message using messaging layer"""
        from src.messaging.protocol import create_message, MessageType

        # Determine message type from dict
        msg_type = MessageType(message.get('type', 'task_request'))

        # Create and send message
        msg = create_message(
            msg_type=msg_type,
            sender=self.agent_id,
            recipient=peer,
            **message
        )

        return await self.messaging.send_message(msg)

    async def start_listening(self, on_task_request: Optional[Callable] = None):
        """
        Start listening for incoming messages

        Args:
            on_task_request: Optional callback for task requests
                            Should accept (escrow_id, task_description, amount, deadline)
                            and return True to accept, False to reject
        """
        if on_task_request:
            self.message_handler.on_task_request(on_task_request)

        # Start listening in background
        await self.messaging.start_listening()

    def set_task_handler(self, handler: Callable):
        """
        Set custom task request handler

        Args:
            handler: Async function that handles task requests
                    Should accept (escrow_id, task_description, amount, deadline)
                    and return True to accept, False to reject
        """
        self.message_handler.on_task_request(handler)

    def set_payment_handler(self, handler: Callable):
        """
        Set custom payment notification handler

        Args:
            handler: Async function that handles payment notifications
                    Should accept (escrow_id, amount, tx_hash, from_addr, to_addr)
        """
        self.message_handler.on_payment(handler)

    async def send_task_result(
        self,
        buyer_address: str,
        escrow_id: str,
        result: Dict[str, Any]
    ):
        """
        Send task completion and results to buyer

        Args:
            buyer_address: Buyer's agent address
            escrow_id: Escrow identifier
            result: Task results dictionary
        """
        return await self.messaging.send_task_complete(
            recipient=buyer_address,
            escrow_id=escrow_id,
            result=result
        )

    async def get_paid(self, on_payment: Optional[Callable] = None):
        """
        Listen for payment notifications

        Args:
            on_payment: Callback for payments (escrow_id, amount, tx_hash, from_addr, to_addr)
        """
        if on_payment:
            self.set_payment_handler(on_payment)
        await self.start_listening()
