"""
Test configuration and fixtures for HYPHA tests
"""

import pytest
import os
from unittest.mock import patch, Mock
from web3 import Web3


@pytest.fixture(scope="session")
def test_env():
    """Test environment variables"""
    env = {
        'PRIVATE_KEY': '0x' + 'a' * 64,
        'ESCROW_CONTRACT_ADDRESS': '0x' + 'b' * 40,
        'USDT_CONTRACT_ADDRESS': '0x' + 'c' * 40,
        'WEB3_PROVIDER_URI': 'https://sepolia.base.org'
    }
    with patch.dict(os.environ, env, clear=False):
        yield env


@pytest.fixture
def mock_web3():
    """Mock Web3 instance"""
    mock_w3 = Mock(spec=Web3)
    mock_w3.is_connected.return_value = True
    mock_w3.eth.block_number = 12345
    mock_w3.eth.gas_price = 1000000000
    mock_w3.eth.get_balance.return_value = Web3.to_wei(1, 'ether')
    mock_w3.eth.get_transaction_count.return_value = 0
    mock_w3.from_wei = Web3.from_wei
    mock_w3.to_wei = Web3.to_wei
    mock_w3.to_checksum_address = Web3.to_checksum_address
    return mock_w3


@pytest.fixture
def mock_account():
    """Mock Ethereum account"""
    mock_acct = Mock()
    mock_acct.address = '0x' + 'd' * 40
    mock_acct.sign_transaction.return_value.raw_transaction = b'signed_tx'
    return mock_acct


@pytest.fixture
def mock_contract():
    """Mock smart contract"""
    mock = Mock()

    # Mock functions
    mock.functions.createEscrow.return_value.build_transaction.return_value = {
        'from': '0x' + 'd' * 40,
        'nonce': 0,
        'gas': 300000,
        'gasPrice': 1000000000
    }

    mock.functions.completeEscrow.return_value.build_transaction.return_value = {
        'from': '0x' + 'd' * 40,
        'nonce': 0,
        'gas': 200000,
        'gasPrice': 1000000000
    }

    mock.functions.getEscrow.return_value.call.return_value = [
        '0x' + 'd' * 40,  # buyer
        '0x' + 'e' * 40,  # provider
        10000000,  # amount (10 USDT in 6 decimals)
        'Test task',  # task
        0,  # status (Active)
        1234567890,  # created_at
        1234654290  # deadline
    ]

    # Mock events
    mock_event = Mock()
    mock_event.process_receipt.return_value = [{
        'args': {
            'escrowId': bytes.fromhex('e' * 64),
            'buyer': '0x' + 'd' * 40,
            'provider': '0x' + 'e' * 40,
            'amount': 10000000,
            'taskDescription': 'Test task'
        }
    }]
    mock.events.EscrowCreated.return_value = mock_event

    return mock


@pytest.fixture
def sample_escrow_id():
    """Sample escrow ID for testing"""
    return '0x' + 'e' * 64


@pytest.fixture
def sample_addresses():
    """Sample Ethereum addresses for testing"""
    return {
        'buyer': '0x' + 'd' * 40,
        'provider': '0x' + 'e' * 40,
        'token': '0x' + 'c' * 40,
        'escrow': '0x' + 'b' * 40
    }
