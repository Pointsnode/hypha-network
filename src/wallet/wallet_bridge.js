#!/usr/bin/env node
/**
 * Tether WDK Wallet Bridge - Production Implementation
 *
 * Provides Python interface to Tether WDK wallet operations
 * Uses official @tetherto/wdk and @tetherto/wdk-wallet-evm packages
 */

const WDK = require('@tetherto/wdk').default;
const { WalletAccountEvm } = require('@tetherto/wdk-wallet-evm');
const { ethers } = require('ethers');

const command = process.argv[2];
const args = process.argv.slice(3);

// Configuration
const NETWORK_CONFIG = {
    base: {
        chainId: 8453,
        rpcUrl: 'https://mainnet.base.org',
        name: 'Base Mainnet'
    },
    baseSepolia: {
        chainId: 84532,
        rpcUrl: 'https://sepolia.base.org',
        name: 'Base Sepolia Testnet'
    }
};

// Use testnet by default for safety, switch to 'base' for mainnet
const CURRENT_NETWORK = process.env.WDK_NETWORK || 'baseSepolia';
const networkConfig = NETWORK_CONFIG[CURRENT_NETWORK];

/**
 * Initialize WDK wallet from seed
 * Converts hex seed to BIP39 mnemonic for WDK compatibility
 */
async function initWallet(seedHex) {
    try {
        // Convert hex seed to mnemonic for WDK
        // WDK expects 12-word mnemonic (128 bits = 16 bytes)
        // Use first 32 hex chars (16 bytes) of the seed
        const seedBuffer = Buffer.from(seedHex.substring(0, 32), 'hex');
        const mnemonic = ethers.Mnemonic.entropyToPhrase(seedBuffer);

        // Create EVM wallet account directly from mnemonic
        // WalletAccountEvm(seed, path, config)
        const walletAccount = new WalletAccountEvm(
            mnemonic,  // seed (mnemonic string)
            '0',       // path (account index)
            {
                rpcUrl: networkConfig.rpcUrl,
                chainId: networkConfig.chainId
            }
        );

        const address = walletAccount.address;

        console.log(JSON.stringify({
            success: true,
            address: address,
            network: CURRENT_NETWORK,
            chainId: networkConfig.chainId,
            networkName: networkConfig.name
        }));
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message,
            stack: process.env.DEBUG ? error.stack : undefined
        }));
    }
}

/**
 * Get USDT balance
 */
async function getBalance(seedHex, address) {
    try {
        // Create provider for USDT contract queries
        const provider = new ethers.JsonRpcProvider(networkConfig.rpcUrl);

        // Convert hex seed to mnemonic for WDK
        // WDK expects 12-word mnemonic (128 bits = 16 bytes)
        // Use first 32 hex chars (16 bytes) of the seed
        const seedBuffer = Buffer.from(seedHex.substring(0, 32), 'hex');
        const mnemonic = ethers.Mnemonic.entropyToPhrase(seedBuffer);

        // Create EVM wallet account directly from mnemonic
        const walletAccount = new WalletAccountEvm(
            mnemonic,
            '0',
            {
                rpcUrl: networkConfig.rpcUrl,
                chainId: networkConfig.chainId
            }
        );

        // USDT contract address on Base
        const USDT_ADDRESS = CURRENT_NETWORK === 'base'
            ? '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'  // Base mainnet USDT
            : '0x036CbD53842c5426634e7929541eC2318f3dCF7e'; // Base Sepolia test USDT

        // USDT has 6 decimals
        const usdtContract = new ethers.Contract(
            USDT_ADDRESS,
            ['function balanceOf(address) view returns (uint256)'],
            provider
        );

        const balance = await usdtContract.balanceOf(address);
        const balanceFormatted = ethers.formatUnits(balance, 6); // USDT has 6 decimals

        console.log(JSON.stringify({
            success: true,
            balance: balanceFormatted,
            currency: 'USDT',
            network: CURRENT_NETWORK,
            usdtAddress: USDT_ADDRESS
        }));
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message,
            stack: process.env.DEBUG ? error.stack : undefined
        }));
    }
}

/**
 * Send USDT payment
 */
async function sendPayment(seedHex, toAddress, amountUSDT) {
    try {
        // Convert hex seed to mnemonic for WDK
        // WDK expects 12-word mnemonic (128 bits = 16 bytes)
        // Use first 32 hex chars (16 bytes) of the seed
        const seedBuffer = Buffer.from(seedHex.substring(0, 32), 'hex');
        const mnemonic = ethers.Mnemonic.entropyToPhrase(seedBuffer);

        // Create EVM wallet account directly from mnemonic
        const walletAccount = new WalletAccountEvm(
            mnemonic,
            '0',
            {
                rpcUrl: networkConfig.rpcUrl,
                chainId: networkConfig.chainId
            }
        );

        // WalletAccountEvm acts as a signer directly
        const signer = walletAccount;

        // USDT contract address on Base
        const USDT_ADDRESS = CURRENT_NETWORK === 'base'
            ? '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'  // Base mainnet USDT
            : '0x036CbD53842c5426634e7929541eC2318f3dCF7e'; // Base Sepolia test USDT

        // USDT contract interface
        const usdtContract = new ethers.Contract(
            USDT_ADDRESS,
            [
                'function transfer(address to, uint256 amount) returns (bool)',
                'function balanceOf(address) view returns (uint256)'
            ],
            signer
        );

        // Convert amount to USDT units (6 decimals)
        const amount = ethers.parseUnits(amountUSDT.toString(), 6);

        // Check balance before sending
        const balance = await usdtContract.balanceOf(walletAccount.address);
        if (balance < amount) {
            throw new Error(`Insufficient balance: ${ethers.formatUnits(balance, 6)} USDT < ${amountUSDT} USDT`);
        }

        // Send transaction
        const tx = await usdtContract.transfer(toAddress, amount);

        // Wait for confirmation
        const receipt = await tx.wait();

        console.log(JSON.stringify({
            success: true,
            txHash: receipt.hash,
            to: toAddress,
            amount: amountUSDT,
            blockNumber: receipt.blockNumber,
            gasUsed: receipt.gasUsed.toString(),
            network: CURRENT_NETWORK
        }));
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message,
            stack: process.env.DEBUG ? error.stack : undefined
        }));
    }
}

// Command routing
(async () => {
    try {
        switch (command) {
            case 'init':
                await initWallet(args[0]);
                break;
            case 'balance':
                await getBalance(args[0], args[1]);
                break;
            case 'send':
                await sendPayment(args[0], args[1], args[2]);
                break;
            default:
                console.log(JSON.stringify({
                    success: false,
                    error: `Unknown command: ${command}. Available: init, balance, send`
                }));
        }
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message,
            stack: process.env.DEBUG ? error.stack : undefined
        }));
    }
})();
