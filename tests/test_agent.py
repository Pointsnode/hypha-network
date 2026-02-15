"""
Unit tests for HYPHA Agent class
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from hypha_sdk import Agent
from web3 import Web3


class TestAgentInitialization:
    """Test Agent initialization"""

    def test_agent_with_seed_is_deterministic(self, test_env):
        """Agents with same seed should have same ID"""
        agent1 = Agent(seed="test-seed-123")
        agent2 = Agent(seed="test-seed-123")
        assert agent1.agent_id == agent2.agent_id

    def test_agent_without_seed_generates_random(self, test_env):
        """Agents without seed should have different IDs"""
        agent1 = Agent()
        agent2 = Agent()
        assert agent1.agent_id != agent2.agent_id

    def test_agent_has_account_when_private_key_set(self, test_env):
        """Agent should create account from PRIVATE_KEY env var"""
        agent = Agent()
        assert agent.account is not None
        assert agent.account.address is not None

    def test_agent_no_account_without_private_key(self):
        """Agent should have no account if PRIVATE_KEY not set"""
        with patch.dict(os.environ, {}, clear=True):
            agent = Agent()
            assert agent.account is None

    def test_agent_loads_contract_addresses(self, test_env):
        """Agent should load contract addresses from env"""
        agent = Agent()
        assert agent.escrow_address == test_env['ESCROW_CONTRACT_ADDRESS']
        assert agent.usdt_address == test_env['USDT_CONTRACT_ADDRESS']

    def test_agent_creates_web3_connection(self, test_env):
        """Agent should create Web3 connection"""
        agent = Agent()
        assert agent.w3 is not None
        assert hasattr(agent.w3, 'eth')


class TestInputValidation:
    """Test input validation for Agent methods"""

    @pytest.mark.asyncio
    async def test_hire_rejects_invalid_address(self, test_env):
        """hire() should reject invalid Ethereum addresses"""
        agent = Agent()
        with pytest.raises(ValueError, match="Invalid peer address"):
            await agent.hire("not-an-address", 10.0, "Task")

    @pytest.mark.asyncio
    async def test_hire_rejects_address_without_0x(self, test_env):
        """hire() should reject addresses without 0x prefix"""
        agent = Agent()
        with pytest.raises(ValueError, match="Invalid peer address"):
            await agent.hire("d" * 40, 10.0, "Task")

    @pytest.mark.asyncio
    async def test_hire_accepts_valid_address(self, test_env, sample_addresses):
        """hire() should accept valid Ethereum addresses"""
        agent = Agent()

        # Mock the internal methods
        with patch.object(agent, '_create_escrow', new_callable=AsyncMock) as mock_create:
            with patch.object(agent, '_send_message', new_callable=AsyncMock) as mock_send:
                mock_create.return_value = '0x' + 'e' * 64

                escrow_id = await agent.hire(
                    sample_addresses['provider'],
                    10.0,
                    "Test task"
                )

                assert escrow_id.startswith('0x')
                assert len(escrow_id) == 66  # 0x + 64 hex chars

    @pytest.mark.asyncio
    async def test_hire_requires_account(self, test_env):
        """hire() should fail if no account configured"""
        with patch.dict(os.environ, {}, clear=True):
            agent = Agent()
            with pytest.raises(ValueError, match="No account configured"):
                await agent.hire("0x" + "d" * 40, 10.0, "Task")

    @pytest.mark.asyncio
    async def test_hire_requires_escrow_contract(self, test_env):
        """hire() should fail if no escrow contract configured"""
        with patch.dict(os.environ, {'PRIVATE_KEY': '0x' + 'a' * 64}, clear=True):
            agent = Agent()
            with pytest.raises(ValueError, match="No escrow contract configured"):
                await agent.hire("0x" + "d" * 40, 10.0, "Task")


class TestEscrowOperations:
    """Test escrow-related operations"""

    @pytest.mark.asyncio
    async def test_create_escrow_generates_id(self, test_env, sample_addresses, mock_contract):
        """_create_escrow should generate proper escrow ID from events"""
        agent = Agent()
        agent.escrow_contract = mock_contract

        # Mock transaction
        mock_receipt = Mock()
        mock_receipt.logs = []

        with patch.object(agent.account, 'sign_transaction') as mock_sign:
            with patch.object(agent.w3.eth, 'send_raw_transaction') as mock_send:
                with patch.object(agent.w3.eth, 'wait_for_transaction_receipt') as mock_wait:
                    mock_sign.return_value.raw_transaction = b'signed_tx'
                    mock_send.return_value.hex.return_value = '0x' + 'f' * 64
                    mock_wait.return_value = mock_receipt

                    escrow_id = await agent._create_escrow(
                        sample_addresses['provider'],
                        10000000,  # 10 USDT
                        "Test task",
                        1234567890
                    )

                    assert escrow_id == '0x' + 'e' * 64
                    mock_contract.events.EscrowCreated.assert_called_once()

    def test_get_escrow_status_returns_details(self, test_env, sample_escrow_id, mock_contract):
        """get_escrow_status should return escrow details"""
        agent = Agent()
        agent.escrow_contract = mock_contract

        status = agent.get_escrow_status(sample_escrow_id)

        assert 'buyer' in status
        assert 'provider' in status
        assert 'amount' in status
        assert status['amount'] == 10.0  # Converted from 10000000 with 6 decimals
        assert status['task'] == 'Test task'
        assert status['status'] == 'Active'

    def test_get_escrow_status_fails_without_contract(self, test_env, sample_escrow_id):
        """get_escrow_status should fail if no contract configured"""
        with patch.dict(os.environ, {'PRIVATE_KEY': '0x' + 'a' * 64}, clear=True):
            agent = Agent()
            with pytest.raises(ValueError, match="No escrow contract configured"):
                agent.get_escrow_status(sample_escrow_id)

    @pytest.mark.asyncio
    async def test_complete_task_releases_payment(self, test_env, sample_escrow_id, mock_contract):
        """complete_task should release payment to provider"""
        agent = Agent()
        agent.escrow_contract = mock_contract

        mock_receipt = Mock()
        mock_receipt.status = 1

        with patch.object(agent.account, 'sign_transaction') as mock_sign:
            with patch.object(agent.w3.eth, 'send_raw_transaction') as mock_send:
                with patch.object(agent.w3.eth, 'wait_for_transaction_receipt') as mock_wait:
                    mock_sign.return_value.raw_transaction = b'signed_tx'
                    mock_send.return_value.hex.return_value = '0x' + 'f' * 64
                    mock_wait.return_value = mock_receipt

                    receipt = await agent.complete_task(sample_escrow_id)

                    assert receipt.status == 1
                    mock_contract.functions.completeEscrow.assert_called_once()


class TestBalanceCheck:
    """Test balance checking"""

    def test_check_balance_returns_eth_amount(self, test_env):
        """check_balance should return ETH balance"""
        agent = Agent()

        with patch.object(agent.w3.eth, 'get_balance') as mock_balance:
            mock_balance.return_value = Web3.to_wei(2.5, 'ether')

            balance = agent.check_balance()

            assert balance == 2.5
            mock_balance.assert_called_once_with(agent.account.address)

    def test_check_balance_returns_zero_without_account(self):
        """check_balance should return 0 if no account"""
        with patch.dict(os.environ, {}, clear=True):
            agent = Agent()
            balance = agent.check_balance()
            assert balance == 0.0


class TestMessageHandlers:
    """Test message handler configuration"""

    def test_set_task_handler(self, test_env):
        """set_task_handler should register custom handler"""
        agent = Agent()

        async def custom_handler(escrow_id, task, amount, deadline, requirements=None):
            return True

        agent.set_task_handler(custom_handler)

        # Verify handler was registered
        assert agent.message_handler._task_request_handler == custom_handler

    def test_set_payment_handler(self, test_env):
        """set_payment_handler should register custom handler"""
        agent = Agent()

        async def custom_handler(escrow_id, amount, tx_hash, from_addr, to_addr):
            pass

        agent.set_payment_handler(custom_handler)

        # Verify handler was registered
        assert agent.message_handler._payment_handler == custom_handler

    @pytest.mark.asyncio
    async def test_get_paid_sets_handler_and_listens(self, test_env):
        """get_paid should set payment handler and start listening"""
        agent = Agent()

        async def payment_handler(escrow_id, amount, tx_hash, from_addr, to_addr):
            pass

        with patch.object(agent, 'set_payment_handler') as mock_set:
            with patch.object(agent, 'start_listening', new_callable=AsyncMock) as mock_listen:
                await agent.get_paid(payment_handler)

                mock_set.assert_called_once_with(payment_handler)
                mock_listen.assert_called_once()


class TestP2POperations:
    """Test P2P discovery and messaging"""

    @pytest.mark.asyncio
    async def test_announce_joins_network(self, test_env):
        """announce should join P2P network on topic"""
        agent = Agent()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"success": true}'

            result = await agent.announce("test-topic")

            assert result == {"success": True}
            assert agent._connected is True

    @pytest.mark.asyncio
    async def test_discover_peers_finds_agents(self, test_env):
        """discover_peers should find other agents on network"""
        agent = Agent()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[{"id": "peer1"}, {"id": "peer2"}]'

            peers = await agent.discover_peers("test-topic")

            assert len(peers) == 2
            assert peers[0]['id'] == 'peer1'

    @pytest.mark.asyncio
    async def test_send_task_result_sends_completion(self, test_env, sample_addresses, sample_escrow_id):
        """send_task_result should send completion message"""
        agent = Agent()

        with patch.object(agent.messaging, 'send_task_complete', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await agent.send_task_result(
                sample_addresses['buyer'],
                sample_escrow_id,
                {"status": "complete", "data": "result"}
            )

            assert result is True
            mock_send.assert_called_once()


class TestKeyDerivation:
    """Test cryptographic key derivation"""

    def test_seed_generates_deterministic_keys(self, test_env):
        """Same seed should produce same keypair"""
        agent1 = Agent(seed="test-seed")
        agent2 = Agent(seed="test-seed")

        assert agent1.keypair['public'] == agent2.keypair['public']
        assert agent1.keypair['secret'] == agent2.keypair['secret']

    def test_different_seeds_produce_different_keys(self, test_env):
        """Different seeds should produce different keypairs"""
        agent1 = Agent(seed="seed-1")
        agent2 = Agent(seed="seed-2")

        assert agent1.keypair['public'] != agent2.keypair['public']
        assert agent1.keypair['secret'] != agent2.keypair['secret']

    def test_agent_id_derived_from_public_key(self, test_env):
        """Agent ID should be first 16 chars of public key"""
        agent = Agent(seed="test-seed")

        assert agent.agent_id == agent.keypair['public'][:16]
        assert len(agent.agent_id) == 16
