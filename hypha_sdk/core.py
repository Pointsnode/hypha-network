"""
HYPHA Unified SDK — Pure Python (no Node.js)
Three-line API for autonomous agent coordination
"""

import os
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from web3 import Web3
from web3.contract import Contract
from dotenv import load_dotenv

from .protocol import Message, MessageType, create_message
from .transport import MessageTransport
from .discovery import Discovery
from .seed_manager import SeedManager
from .wallet_wdk import Wallet
from .validation import (
    validate_ethereum_address, validate_amount, validate_private_key,
    validate_escrow_id, validate_task_description, validate_deadline_hours,
    validate_seed, ValidationError,
)
from .logging_config import logger

load_dotenv()


def _load_contract_abi(abi_name: str) -> list:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    abi_path = os.path.join(current_dir, 'abis', f'{abi_name}.json')
    if not os.path.exists(abi_path):
        raise FileNotFoundError(f"ABI file not found: {abi_path}")
    with open(abi_path, 'r') as f:
        return json.load(f)


class Agent:
    """Unified HYPHA agent with P2P + Payments"""

    def __init__(self, seed: Optional[str] = None, web3_provider: Optional[str] = None):
        if seed is not None:
            try:
                seed = validate_seed(seed)
            except ValidationError as e:
                logger.error(f"Invalid seed: {e}")
                raise ValueError(str(e)) from e

        # Unified seed manager — one seed for identity + wallet
        self.seed_manager = SeedManager.from_string(seed) if seed else SeedManager()
        self.agent_id = self.seed_manager.node_id_hex

        logger.debug(f"Initialized agent with ID: {self.agent_id}")

        # Web3 setup
        provider_uri = web3_provider or os.getenv('WEB3_PROVIDER_URI', 'https://sepolia.base.org')
        self.w3 = Web3(Web3.HTTPProvider(provider_uri))

        # Wallet: use PRIVATE_KEY env var if set, otherwise derive from seed
        private_key = os.getenv('PRIVATE_KEY')
        if private_key:
            try:
                private_key = validate_private_key(private_key)
            except ValidationError as e:
                logger.error(f"Invalid PRIVATE_KEY in environment: {e}")
                raise ValueError(f"Invalid PRIVATE_KEY: {e}") from e
        else:
            private_key = self.seed_manager.wallet_private_key

        self.account = self.w3.eth.account.from_key(private_key)
        logger.info(f"Wallet address: {self.account.address}")

        # Pure Python wallet for USDT payments
        self.wallet = Wallet(
            private_key=private_key,
            web3_provider=provider_uri,
            usdt_address=os.getenv('USDT_CONTRACT_ADDRESS'),
        )

        self.escrow_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
        self.escrow_contract = self._load_escrow_contract() if self.escrow_address else None

        self._connected = False
        self._topic = "hypha-agents"

        # Pure-Python messaging & discovery
        private_key_bytes = bytes.fromhex(private_key.replace('0x', ''))
        self.messaging = MessageTransport(self.agent_id, private_key_bytes)
        # Use first 20 bytes of node_id for Kademlia (requires 20-byte ID)
        kademlia_node_id = self.seed_manager.node_id[:20]
        self.discovery = Discovery(node_id=kademlia_node_id)

    def _load_escrow_contract(self) -> Optional[Contract]:
        if not self.escrow_address:
            return None
        try:
            abi = _load_contract_abi('escrow_abi')
            return self.w3.eth.contract(
                address=Web3.to_checksum_address(self.escrow_address), abi=abi)
        except Exception as e:
            logger.error(f"Failed to load escrow contract: {e}")
            raise

    # ── P2P Discovery (pure Python) ──────────────────────────

    async def announce(self, topic: Optional[str] = None):
        topic = topic or self._topic
        logger.info(f"Announcing on P2P network: {topic}")
        agent_info = {
            "agent_id": self.agent_id,
            "wallet_address": self.account.address,
        }
        await self.discovery.announce(topic, agent_info)
        self._connected = True
        logger.info(f"Successfully announced on {topic}")
        return agent_info

    async def discover_peers(self, topic: Optional[str] = None) -> list:
        topic = topic or self._topic
        logger.info(f"Discovering peers on topic: {topic}")
        peers = await self.discovery.discover_peers(topic)
        logger.info(f"Discovered {len(peers)} peers")
        return peers

    # ── Hiring / Escrow ──────────────────────────────────────

    async def hire(self, peer: str, amount: float, task: str, deadline_hours: int = 24) -> str:
        if not self.account:
            raise ValueError("No account configured. Set PRIVATE_KEY in .env")
        if not self.escrow_contract:
            raise ValueError("No escrow contract configured. Set ESCROW_CONTRACT_ADDRESS in .env")

        try:
            peer_address = validate_ethereum_address(peer, "peer")
            validated_amount = validate_amount(amount, "amount")
            validated_task = validate_task_description(task, "task")
            validated_hours = validate_deadline_hours(deadline_hours, "deadline_hours")
        except ValidationError as e:
            raise ValueError(str(e)) from e

        amount_units = int(validated_amount * 10**6)
        deadline = int((datetime.now() + timedelta(hours=validated_hours)).timestamp())
        escrow_id = await self._create_escrow(peer_address, amount_units, validated_task, deadline)

        try:
            msg = create_message(MessageType.TASK_REQUEST, self.agent_id, peer_address,
                                 escrow_id=escrow_id, task=validated_task,
                                 amount=validated_amount, deadline=deadline)
            await self.messaging.send_message(msg)
        except Exception as e:
            logger.warning(f"Failed to send P2P message: {e}")

        return escrow_id

    async def complete_task(self, escrow_id: str):
        if not self.account or not self.escrow_contract:
            raise ValueError("Agent not properly configured")
        try:
            validated_id = validate_escrow_id(escrow_id, "escrow_id")
        except ValidationError as e:
            raise ValueError(str(e)) from e

        escrow_bytes = bytes.fromhex(validated_id.replace('0x', ''))
        tx = self.escrow_contract.functions.completeEscrow(escrow_bytes).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000, 'gasPrice': self.w3.eth.gas_price,
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def get_escrow_status(self, escrow_id: str) -> Dict[str, Any]:
        if not self.escrow_contract:
            raise ValueError("No escrow contract configured")
        try:
            validated_id = validate_escrow_id(escrow_id, "escrow_id")
        except ValidationError as e:
            raise ValueError(str(e)) from e

        result = self.escrow_contract.functions.getEscrow(
            bytes.fromhex(validated_id.replace('0x', ''))).call()
        status_names = ['Active', 'Completed', 'Disputed', 'Refunded', 'Cancelled']
        return {
            'buyer': result[0], 'provider': result[1],
            'amount': result[2] / 10**6, 'task': result[3],
            'status': status_names[result[4]],
            'created_at': datetime.fromtimestamp(result[5]),
            'deadline': datetime.fromtimestamp(result[6]),
        }

    def check_balance(self) -> float:
        if not self.account:
            return 0.0
        return float(self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether'))

    async def _create_escrow(self, provider, amount, task, deadline) -> str:
        tx = self.escrow_contract.functions.createEscrow(
            provider, amount, task, deadline
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 300000, 'gasPrice': self.w3.eth.gas_price,
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        logs = self.escrow_contract.events.EscrowCreated().process_receipt(receipt)
        if not logs:
            raise RuntimeError("EscrowCreated event not found")
        return logs[0]['args']['escrowId'].hex()

    # ── Messaging helpers ────────────────────────────────────

    async def start_listening(self, on_task_request: Optional[Callable] = None):
        if on_task_request:
            self.messaging.register_handler(MessageType.TASK_REQUEST, on_task_request)
        await self.messaging.start_listening()

    def set_task_handler(self, handler: Callable):
        self.messaging.register_handler(MessageType.TASK_REQUEST, handler)

    def set_payment_handler(self, handler: Callable):
        self.messaging.register_handler(MessageType.PAYMENT_NOTIFICATION, handler)

    async def send_task_result(self, buyer_address: str, escrow_id: str, result: Dict[str, Any]):
        return await self.messaging.send_task_complete(
            recipient=buyer_address, escrow_id=escrow_id, result=result)

    async def get_paid(self, on_payment: Optional[Callable] = None):
        if on_payment:
            self.set_payment_handler(on_payment)
        await self.start_listening()
