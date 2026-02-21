import { ethers } from 'ethers'
import { execSync } from 'child_process'
import { readFileSync, mkdirSync, writeFileSync } from 'fs'

// ── Config ─────────────────────────────────────────────────────────────────
const NETWORK   = process.env.NETWORK || 'testnet'  // 'testnet' or 'mainnet'
const IS_MAINNET = NETWORK === 'mainnet'

const RPC = IS_MAINNET
  ? 'https://mainnet.base.org'
  : 'https://sepolia.base.org'

// USDC addresses
const USDC = IS_MAINNET
  ? '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'  // Base mainnet USDC
  : '0x036CbD53842c5426634e7929541eC2318f3dCF7e'  // Base Sepolia USDC

const PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY
const TREASURY    = process.env.TREASURY_ADDRESS

if (!PRIVATE_KEY) { console.error('Set DEPLOYER_PRIVATE_KEY'); process.exit(1) }
if (!TREASURY)    { console.error('Set TREASURY_ADDRESS'); process.exit(1) }

// ── Compile ────────────────────────────────────────────────────────────────
console.log(`\n[deploy] Compiling HyphaNetwork.sol...`)
mkdirSync('./deploy/out', { recursive: true })
execSync('solc --abi --bin --overwrite -o ./deploy/out ./contracts/HyphaNetwork.sol', { stdio: 'inherit' })

const abi      = JSON.parse(readFileSync('./deploy/out/HyphaNetwork.abi', 'utf8'))
const bytecode = '0x' + readFileSync('./deploy/out/HyphaNetwork.bin', 'utf8').trim()

// ── Deploy ─────────────────────────────────────────────────────────────────
const provider = new ethers.JsonRpcProvider(RPC)
const signer   = new ethers.Wallet(PRIVATE_KEY, provider)
const balance  = await provider.getBalance(signer.address)

console.log(`[deploy] Network  : ${IS_MAINNET ? 'Base Mainnet' : 'Base Sepolia'}`)
console.log(`[deploy] Deployer : ${signer.address}`)
console.log(`[deploy] Balance  : ${ethers.formatEther(balance)} ETH`)
console.log(`[deploy] USDC     : ${USDC}`)
console.log(`[deploy] Treasury : ${TREASURY}`)

if (balance < ethers.parseEther('0.003')) {
  console.error('[deploy] ❌ Insufficient ETH. Need at least 0.003 ETH for gas.')
  process.exit(1)
}

const factory  = new ethers.ContractFactory(abi, bytecode, signer)
console.log('\n[deploy] Deploying...')
const contract = await factory.deploy(USDC, TREASURY)
await contract.waitForDeployment()

const address = await contract.getAddress()
const receipt = await provider.getTransactionReceipt(contract.deploymentTransaction().hash)

console.log(`\n[deploy] ✅ HyphaNetwork deployed!`)
console.log(`[deploy]   Address  : ${address}`)
console.log(`[deploy]   Tx       : ${contract.deploymentTransaction().hash}`)
console.log(`[deploy]   Gas used : ${receipt.gasUsed.toString()}`)
console.log(`[deploy]   Explorer : ${IS_MAINNET ? 'https://basescan.org' : 'https://sepolia.basescan.org'}/address/${address}`)

// Save deployment info
const info = { network: NETWORK, address, usdc: USDC, treasury: TREASURY, deployedAt: new Date().toISOString(), tx: contract.deploymentTransaction().hash }
writeFileSync(`./deploy/${NETWORK}-deployment.json`, JSON.stringify(info, null, 2))
console.log(`\n[deploy] Saved to deploy/${NETWORK}-deployment.json`)
console.log(`\n[deploy] Next steps:`)
console.log(`[deploy]   1. Set CONTRACT_ADDRESS=${address} in Railway env vars`)
console.log(`[deploy]   2. Update dashboard contract address`)
console.log(`[deploy]   3. Update hypha-sdk default contract address`)
