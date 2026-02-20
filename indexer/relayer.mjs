import { ethers } from 'ethers'
import http from 'http'

// ── Config ────────────────────────────────────────────────────────────────────
const RPC         = process.env.RPC_URL          || 'https://sepolia.base.org'
const CONTRACT    = process.env.CONTRACT_ADDRESS || '0xf1cF5A40ad2c48456C2aD4d59554Ad9baa51F644'
const RELAYER_KEY = process.env.RELAYER_PRIVATE_KEY
const PORT        = process.env.PORT || process.env.RELAYER_PORT || 3000

const ABI = [
  'function registerAgentFor(address agent, bytes32 pubkey) external',
  'function agents(address) view returns (bool registered, bytes32 pubkey, uint256 reputation)',
  'function listService(string calldata serviceType, uint256 price) external',
  'event AgentRegistered(address indexed agent, bytes32 pubkey)',
  'event ServiceListed(address indexed agent, string serviceType, uint256 price)',
  'event EscrowCreated(bytes32 indexed taskId, address client, address provider, uint256 amount)',
  'event EscrowReleased(bytes32 indexed taskId, uint256 amount)'
]

const DEPLOY_BLOCK = 37850000 // new contract deployed Feb 20 2026 (~block 37.85M)

if (!RELAYER_KEY) {
  console.error('[relayer] RELAYER_PRIVATE_KEY not set — relayer disabled')
  process.exit(1)
}

const provider = new ethers.JsonRpcProvider(RPC)
const signer   = new ethers.Wallet(RELAYER_KEY, provider)
const contract = new ethers.Contract(CONTRACT, ABI, signer)

console.log(`[relayer] Gas tank: ${signer.address}`)
console.log(`[relayer] Contract: ${CONTRACT}`)
console.log(`[relayer] Listening on port ${PORT}`)

// ── Rate limiting (in-memory, resets on restart) ──────────────────────────────
const recentAddresses = new Map() // address → timestamp
const COOLDOWN_MS = 60 * 60 * 1000 // 1 hour between registrations per address

function isRateLimited(address) {
  const last = recentAddresses.get(address)
  if (!last) return false
  return Date.now() - last < COOLDOWN_MS
}

// ── CORS headers ──────────────────────────────────────────────────────────────
function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
}

function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' })
  res.end(JSON.stringify(body))
}

// ── HTTP Server ───────────────────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  setCors(res)

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204)
    res.end()
    return
  }

  // Health check
  if (req.method === 'GET' && req.url === '/health') {
    const balance = await provider.getBalance(signer.address)
    return json(res, 200, {
      status: 'ok',
      contract: CONTRACT,
      gasTank: signer.address,
      balance: ethers.formatEther(balance) + ' ETH'
    })
  }

  // ── POST /api/register ────────────────────────────────────────────────────
  if (req.method === 'POST' && req.url === '/api/register') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', async () => {
      try {
        const { address, pubkey } = JSON.parse(body)

        // Validate address
        if (!address || !ethers.isAddress(address)) {
          return json(res, 400, { error: 'Invalid agent address' })
        }

        const addr = address.toLowerCase()

        // Rate limit check
        if (isRateLimited(addr)) {
          return json(res, 429, { error: 'Rate limited. Try again in 1 hour.' })
        }

        // Check if already registered on-chain
        const info = await contract.agents(address)
        if (info.registered) {
          return json(res, 200, {
            success: true,
            alreadyRegistered: true,
            message: 'Agent already registered on HYPHA'
          })
        }

        // Build pubkey bytes32
        const pkLabel = pubkey || addr.slice(0, 31)
        const pkBytes = ethers.encodeBytes32String(pkLabel.slice(0, 31))

        // Check gas tank balance
        const balance = await provider.getBalance(signer.address)
        if (balance < ethers.parseEther('0.00005')) {
          return json(res, 503, { error: 'Gas tank low. Try again later.' })
        }

        // ✅ THE FIX: call registerAgentFor(agentAddress, pubkey)
        // This registers the AGENT's address on-chain, NOT the relayer's address
        console.log(`[relayer] Registering agent ${addr}`)
        const tx = await contract.registerAgentFor(address, pkBytes)
        await tx.wait()

        recentAddresses.set(addr, Date.now())

        console.log(`[relayer] ✅ Registered ${addr} — tx: ${tx.hash}`)
        return json(res, 200, {
          success: true,
          txHash: tx.hash,
          explorer: `https://sepolia.basescan.org/tx/${tx.hash}`,
          message: 'Agent registered on HYPHA!'
        })

      } catch (e) {
        console.error('[relayer] Error:', e.message)
        return json(res, 500, { error: e.message || 'Registration failed' })
      }
    })
    return
  }

  // ── GET /api/stats ─────────────────────────────────────────────────────────
  if (req.method === 'GET' && req.url === '/api/stats') {
    try {
      const currentBlock = await provider.getBlockNumber()
      const CHUNK = 9000

      // Query all events in chunks to avoid eth_getLogs range limit
      async function queryAllChunks(filter) {
        const events = []
        for (let from = DEPLOY_BLOCK; from <= currentBlock; from += CHUNK) {
          const to = Math.min(from + CHUNK - 1, currentBlock)
          const chunk = await contract.queryFilter(filter, from, to)
          events.push(...chunk)
        }
        return events
      }

      const [agentEvents, escrowCreated, escrowReleased] = await Promise.all([
        queryAllChunks(contract.filters.AgentRegistered()),
        queryAllChunks(contract.filters.EscrowCreated()),
        queryAllChunks(contract.filters.EscrowReleased())
      ])

      const volume = escrowReleased.reduce((sum, e) => sum + Number(ethers.formatEther(e.args.amount)), 0)
      return json(res, 200, {
        agents: agentEvents.length,
        volume: parseFloat(volume.toFixed(6)),
        jobs: escrowReleased.length,
        escrows: escrowCreated.length - escrowReleased.length,
        contract: CONTRACT,
        block: currentBlock
      })
    } catch (e) {
      return json(res, 500, { error: e.message })
    }
  }

  // ── GET /api/agents ──────────────────────────────────────────────────────
  if (req.method === 'GET' && req.url === '/api/agents') {
    try {
      const currentBlock = await provider.getBlockNumber()
      const CHUNK = 9000
      const events = []
      for (let from = DEPLOY_BLOCK; from <= currentBlock; from += CHUNK) {
        const to = Math.min(from + CHUNK - 1, currentBlock)
        const chunk = await contract.queryFilter(contract.filters.AgentRegistered(), from, to)
        events.push(...chunk)
      }
      const agents = events.map(e => ({
        address: e.args.agent,
        pubkey: ethers.decodeBytes32String(e.args.pubkey).replace(/\0/g, ''),
        block: e.blockNumber,
        tx: e.transactionHash
      }))
      return json(res, 200, { agents, total: agents.length })
    } catch (e) {
      return json(res, 500, { error: e.message })
    }
  }

  // ── GET /api/services ────────────────────────────────────────────────────
  if (req.method === 'GET' && req.url === '/api/services') {
    try {
      const currentBlock = await provider.getBlockNumber()
      const CHUNK = 9000
      const events = []
      for (let from = DEPLOY_BLOCK; from <= currentBlock; from += CHUNK) {
        const to = Math.min(from + CHUNK - 1, currentBlock)
        const chunk = await contract.queryFilter(contract.filters.ServiceListed(), from, to)
        events.push(...chunk)
      }
      // Deduplicate — keep latest listing per agent+serviceType
      const seen = new Map()
      for (const e of events) {
        const key = `${e.args.agent}-${e.args.serviceType}`
        seen.set(key, {
          agent: e.args.agent,
          serviceType: e.args.serviceType,
          price_eth: ethers.formatEther(e.args.price),
          block: e.blockNumber,
          tx: e.transactionHash
        })
      }
      const services = Array.from(seen.values())
      return json(res, 200, { services, total: services.length })
    } catch (e) {
      return json(res, 500, { error: e.message })
    }
  }

  // ── POST /api/service ────────────────────────────────────────────────────
  // Agents can list a service (relayer sponsors the gas)
  if (req.method === 'POST' && req.url === '/api/service') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', async () => {
      try {
        const { address, serviceType, price_eth } = JSON.parse(body)
        if (!address || !ethers.isAddress(address)) return json(res, 400, { error: 'Invalid address' })
        if (!serviceType) return json(res, 400, { error: 'serviceType required' })

        // Check agent is registered
        const info = await contract.agents(address)
        if (!info.registered) return json(res, 400, { error: 'Agent not registered. Call /api/register first.' })

        const priceWei = ethers.parseEther(String(price_eth || '0'))
        const balance = await provider.getBalance(signer.address)
        if (balance < ethers.parseEther('0.00005')) return json(res, 503, { error: 'Gas tank low.' })

        console.log(`[relayer] Listing service "${serviceType}" for ${address}`)
        const tx = await contract.listService(serviceType, priceWei)
        await tx.wait()

        console.log(`[relayer] ✅ Service listed — tx: ${tx.hash}`)
        return json(res, 200, {
          success: true,
          txHash: tx.hash,
          explorer: `https://sepolia.basescan.org/tx/${tx.hash}`,
          message: `Service "${serviceType}" listed on HYPHA!`
        })
      } catch (e) {
        console.error('[relayer] Service error:', e.message)
        return json(res, 500, { error: e.message })
      }
    })
    return
  }

  // 404
  json(res, 404, { error: 'Not found' })
})

server.listen(PORT, () => {
  console.log(`[relayer] 🚀 Ready on port ${PORT}`)
})
