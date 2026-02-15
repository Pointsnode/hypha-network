"""
Health check utilities for HYPHA SDK

Provides system health monitoring and diagnostics
"""

from typing import Dict, Any
import time
from .logging_config import logger


class HealthCheck:
    """System health checker for HYPHA agent"""

    def __init__(self, agent):
        """
        Initialize health checker

        Args:
            agent: HYPHA Agent instance to check
        """
        self.agent = agent

    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks

        Returns:
            Dictionary with health status for all components
        """
        logger.debug("Running health checks...")

        health = {
            'timestamp': int(time.time()),
            'overall': 'unknown',
            'web3': self.check_web3(),
            'account': self.check_account(),
            'contracts': self.check_contracts(),
            'messaging': self.check_messaging()
        }

        # Determine overall health
        statuses = [
            health['web3']['status'],
            health['account']['status'],
            health['contracts']['status'],
            health['messaging']['status']
        ]

        if all(s == 'healthy' for s in statuses):
            health['overall'] = 'healthy'
        elif 'unhealthy' in statuses:
            health['overall'] = 'unhealthy'
        else:
            health['overall'] = 'degraded'

        logger.info(f"Health check complete: {health['overall']}")

        return health

    def check_web3(self) -> Dict[str, Any]:
        """
        Check Web3 connection

        Returns:
            Web3 health status
        """
        try:
            connected = self.agent.w3.is_connected()

            if connected:
                block_number = self.agent.w3.eth.block_number
                gas_price = self.agent.w3.eth.gas_price

                return {
                    'status': 'healthy',
                    'connected': True,
                    'block_number': block_number,
                    'gas_price_gwei': gas_price / 10**9,
                    'provider': str(self.agent.w3.provider)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'connected': False,
                    'error': 'Not connected to Web3 provider'
                }

        except Exception as e:
            logger.error(f"Web3 health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }

    def check_account(self) -> Dict[str, Any]:
        """
        Check account configuration

        Returns:
            Account health status
        """
        if not self.agent.account:
            return {
                'status': 'unconfigured',
                'configured': False,
                'message': 'No PRIVATE_KEY set in environment'
            }

        try:
            balance_wei = self.agent.w3.eth.get_balance(self.agent.account.address)
            balance_eth = float(self.agent.w3.from_wei(balance_wei, 'ether'))

            status = 'healthy'
            warnings = []

            # Warn if balance is low
            if balance_eth < 0.001:
                warnings.append('Low ETH balance - may not have enough for gas')
                status = 'degraded'

            return {
                'status': status,
                'configured': True,
                'address': self.agent.account.address,
                'balance_eth': balance_eth,
                'warnings': warnings if warnings else None
            }

        except Exception as e:
            logger.error(f"Account health check failed: {e}")
            return {
                'status': 'unhealthy',
                'configured': True,
                'error': str(e)
            }

    def check_contracts(self) -> Dict[str, Any]:
        """
        Check contract configuration

        Returns:
            Contract health status
        """
        escrow_status = {
            'configured': bool(self.agent.escrow_address),
            'address': self.agent.escrow_address
        }

        usdt_status = {
            'configured': bool(self.agent.usdt_address),
            'address': self.agent.usdt_address
        }

        # Check if contract is actually deployed
        if self.agent.escrow_address:
            try:
                code = self.agent.w3.eth.get_code(self.agent.escrow_address)
                escrow_status['deployed'] = len(code) > 0
                if not escrow_status['deployed']:
                    escrow_status['error'] = 'No code at contract address'
            except Exception as e:
                escrow_status['deployed'] = False
                escrow_status['error'] = str(e)

        if self.agent.usdt_address:
            try:
                code = self.agent.w3.eth.get_code(self.agent.usdt_address)
                usdt_status['deployed'] = len(code) > 0
                if not usdt_status['deployed']:
                    usdt_status['error'] = 'No code at contract address'
            except Exception as e:
                usdt_status['deployed'] = False
                usdt_status['error'] = str(e)

        # Determine overall status
        if escrow_status.get('configured') and usdt_status.get('configured'):
            if escrow_status.get('deployed') and usdt_status.get('deployed'):
                status = 'healthy'
            else:
                status = 'unhealthy'
        elif escrow_status.get('configured') or usdt_status.get('configured'):
            status = 'partial'
        else:
            status = 'unconfigured'

        return {
            'status': status,
            'escrow': escrow_status,
            'usdt': usdt_status
        }

    def check_messaging(self) -> Dict[str, Any]:
        """
        Check messaging layer status

        Returns:
            Messaging health status
        """
        try:
            # Check if messaging transport is initialized
            if not self.agent.messaging:
                return {
                    'status': 'unconfigured',
                    'initialized': False
                }

            # Check if agent has ID
            if not self.agent.agent_id:
                return {
                    'status': 'unhealthy',
                    'initialized': True,
                    'error': 'No agent ID'
                }

            return {
                'status': 'healthy',
                'initialized': True,
                'agent_id': self.agent.agent_id,
                'connected': self.agent._connected
            }

        except Exception as e:
            logger.error(f"Messaging health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def get_summary(self, health_data: Dict[str, Any]) -> str:
        """
        Get human-readable health summary

        Args:
            health_data: Health check results from check_all()

        Returns:
            Formatted summary string
        """
        lines = [
            f"HYPHA Health Check - {health_data['overall'].upper()}",
            f"Timestamp: {health_data['timestamp']}",
            "",
            f"Web3: {health_data['web3']['status']}",
            f"Account: {health_data['account']['status']}",
            f"Contracts: {health_data['contracts']['status']}",
            f"Messaging: {health_data['messaging']['status']}",
        ]

        if health_data['account'].get('address'):
            lines.append(f"\nAccount: {health_data['account']['address']}")
            lines.append(f"Balance: {health_data['account'].get('balance_eth', 0):.4f} ETH")

        if health_data['web3'].get('block_number'):
            lines.append(f"\nBlock: {health_data['web3']['block_number']}")
            lines.append(f"Gas Price: {health_data['web3'].get('gas_price_gwei', 0):.2f} Gwei")

        return "\n".join(lines)
