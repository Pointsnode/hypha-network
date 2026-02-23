import { ethers } from 'ethers'
import http from 'http'
import pg from 'pg'

const { Pool } = pg

// ── Config ────────────────────────────────────────────────────────────────────
const RPC         = process.env.RPC_URL          || 'https://mainnet.base.org'
const CONTRACT    = process.env.CONTRACT_ADDRESS || '0xf1cF5A40ad2c48456C2aD4d59554Ad9baa51F644'
const RELAYER_KEY = process.env.RELAYER_PRIVATE_KEY
const PORT        = process.env.PORT || 3000
const DATABASE_URL = process.env.DATABASE_URL

const DEPLOY_BLOCK = 37930000

const ABI = [
  'function registerAgentFor(address agent, bytes32 pubkey) external',
  'function agents(address) view returns (bool registered, bytes32 pubkey, uint256 reputation)',
  'function listService(string calldata serviceType, uint256 price) external',
  'function claimBounty(bytes32 id) external',
  'function submitWork(bytes32 id, string calldata result) external',
  'function bounties(bytes32) view returns (address client, address provider, uint256 amount, string description, string result, uint8 status)',
  'event AgentRegistered(address indexed agent, bytes32 pubkey)',
  'event ServiceListed(address indexed agent, string serviceType, uint256 price)',
  'event BountyPosted(bytes32 indexed id, address indexed client, uint256 amount, string description)',
  'event BountyClaimed(bytes32 indexed id, address indexed provider)',
  'event WorkSubmitted(bytes32 indexed id, address indexed provider, string result)',
  'event BountyReleased(bytes32 indexed id, address indexed provider, uint256 amount)',
  'event BountyCancelled(bytes32 indexed id)',
  'event EscrowCreated(bytes32 indexed taskId, address client, address provider, uint256 amount)',
  'event EscrowReleased(bytes32 indexed taskId, uint256 amount)'
]

const BOUNTY_STATUS = ['Open', 'Claimed', 'Submitted', 'Released', 'Cancelled']

if (!RELAYER_KEY) { console.error('[relayer] RELAYER_PRIVATE_KEY not set'); process.exit(1) }

const provider = new ethers.JsonRpcProvider(RPC)
const signer   = new ethers.Wallet(RELAYER_KEY, provider)
const contract = new ethers.Contract(CONTRACT, ABI, signer)

console.log(`[relayer] Gas tank : ${signer.address}`)
console.log(`[relayer] Contract : ${CONTRACT}`)
console.log(`[relayer] Port     : ${PORT}`)

// ── Postgres ──────────────────────────────────────────────────────────────────
let pool = null

async function initDB() {
  if (!DATABASE_URL) {
    console.log('[db] No DATABASE_URL — running without persistence')
    return
  }
  pool = new Pool({ connectionString: DATABASE_URL, ssl: { rejectUnauthorized: false } })

  await pool.query(`
    CREATE TABLE IF NOT EXISTS agents (
      address     TEXT PRIMARY KEY,
      pubkey      TEXT,
      block_number INTEGER,
      tx_hash     TEXT,
      registered_at TIMESTAMPTZ DEFAULT NOW()
    )
  `)
  await pool.query(`
    CREATE TABLE IF NOT EXISTS indexer_state (
      key   TEXT PRIMARY KEY,
      value TEXT
    )
  `)
  console.log('[db] Tables ready')
}

async function dbSaveAgent(address, pubkey, blockNumber, txHash) {
  if (!pool) return
  await pool.query(
    `INSERT INTO agents (address, pubkey, block_number, tx_hash)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (address) DO NOTHING`,
    [address.toLowerCase(), pubkey, blockNumber, txHash]
  )
}

async function dbGetAgents() {
  if (!pool) return null
  const res = await pool.query('SELECT * FROM agents ORDER BY registered_at ASC')
  return res.rows
}

async function dbGetLastBlock() {
  if (!pool) return DEPLOY_BLOCK
  const res = await pool.query(`SELECT value FROM indexer_state WHERE key = 'last_block'`)
  return res.rows.length ? parseInt(res.rows[0].value) : DEPLOY_BLOCK
}

async function dbSetLastBlock(block) {
  if (!pool) return
  await pool.query(
    `INSERT INTO indexer_state (key, value) VALUES ('last_block', $1)
     ON CONFLICT (key) DO UPDATE SET value = $1`,
    [String(block)]
  )
}

// ── Indexer — catch up from last known block ──────────────────────────────────
async function indexAgents() {
  try {
    const currentBlock = await provider.getBlockNumber()
    const fromBlock    = await dbGetLastBlock()
    const CHUNK        = 9000

    console.log(`[indexer] Scanning blocks ${fromBlock} → ${currentBlock}`)
    let count = 0

    for (let from = fromBlock; from <= currentBlock; from += CHUNK) {
      const to     = Math.min(from + CHUNK - 1, currentBlock)
      const events = await contract.queryFilter(contract.filters.AgentRegistered(), from, to)
      for (const e of events) {
        const address = e.args.agent.toLowerCase()
        const pubkey  = ethers.decodeBytes32String(e.args.pubkey).replace(/\0/g, '')
        await dbSaveAgent(address, pubkey, e.blockNumber, e.transactionHash)
        count++
      }
    }

    await dbSetLastBlock(currentBlock)
    console.log(`[indexer] ✅ Indexed ${count} new agents. Total block: ${currentBlock}`)
  } catch (e) {
    console.error('[indexer] Error:', e.message)
  }
}

// ── Rate limiting ─────────────────────────────────────────────────────────────
const recentAddresses = new Map()
const COOLDOWN_MS = 60 * 60 * 1000

function isRateLimited(address) {
  const last = recentAddresses.get(address)
  if (!last) return false
  return Date.now() - last < COOLDOWN_MS
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
}

function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' })
  res.end(JSON.stringify(body))
}

async function queryAllChunks(filter, fromBlock) {
  const currentBlock = await provider.getBlockNumber()
  const CHUNK = 9000
  const events = []
  for (let from = fromBlock || DEPLOY_BLOCK; from <= currentBlock; from += CHUNK) {
    const to = Math.min(from + CHUNK - 1, currentBlock)
    const chunk = await contract.queryFilter(filter, from, to)
    events.push(...chunk)
  }
  return events
}

// ── HTTP Server ───────────────────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  setCors(res)
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return }

  // GET /health
  if (req.method === 'GET' && req.url === '/health') {
    const balance = await provider.getBalance(signer.address)
    return json(res, 200, {
      status: 'ok', contract: CONTRACT,
      gasTank: signer.address,
      balance: ethers.formatEther(balance) + ' ETH',
      db: pool ? 'connected' : 'none'
    })
  }

  // POST /api/register
  if (req.method === 'POST' && req.url === '/api/register') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', async () => {
      try {
        const { address, pubkey } = JSON.parse(body)
        if (!address || !ethers.isAddress(address)) return json(res, 400, { error: 'Invalid agent address' })
        const addr = address.toLowerCase()
        if (isRateLimited(addr)) return json(res, 429, { error: 'Rate limited. Try again in 1 hour.' })

        const info = await contract.agents(address)
        if (info.registered) {
          await dbSaveAgent(addr, pubkey || addr.slice(0, 31), 0, '')
          return json(res, 200, { success: true, alreadyRegistered: true, message: 'Agent already registered on HYPHA' })
        }

        const pkLabel = pubkey || addr.slice(0, 31)
        const pkBytes = ethers.encodeBytes32String(pkLabel.slice(0, 31))
        const balance = await provider.getBalance(signer.address)
        if (balance < ethers.parseEther('0.00005')) return json(res, 503, { error: 'Gas tank low.' })

        console.log(`[relayer] Registering ${addr}`)
        const tx = await contract.registerAgentFor(address, pkBytes)
        await tx.wait()

        recentAddresses.set(addr, Date.now())
        await dbSaveAgent(addr, pkLabel, tx.blockNumber || 0, tx.hash)

        console.log(`[relayer] ✅ Registered ${addr} — tx: ${tx.hash}`)
        return json(res, 200, {
          success: true, txHash: tx.hash,
          explorer: `https://basescan.org/tx/${tx.hash}`,
          message: 'Agent registered on HYPHA!'
        })
      } catch (e) {
        console.error('[relayer] Register error:', e.message)
        return json(res, 500, { error: e.message })
      }
    })
    return
  }

  // GET /api/agents — serve from DB first, fallback to chain
  if (req.method === 'GET' && req.url === '/api/agents') {
    try {
      const dbAgents = await dbGetAgents()
      if (dbAgents && dbAgents.length > 0) {
        const agents = dbAgents.map(a => ({
          address: a.address, pubkey: a.pubkey,
          block: a.block_number, tx: a.tx_hash
        }))
        return json(res, 200, { agents, total: agents.length, source: 'db' })
      }
      // DB empty — return [] rather than hitting rate-limited RPC
      return json(res, 200, { agents: [], total: 0, source: 'db' })
    } catch (e) { return json(res, 500, { error: e.message }) }
  }

  // GET /api/stats
  if (req.method === 'GET' && req.url === '/api/stats') {
    try {
      const currentBlock = await provider.getBlockNumber()
      const dbAgents = await dbGetAgents()
      const agentCount = dbAgents ? dbAgents.length : 0
      const [escrowCreated, escrowReleased] = await Promise.all([
        queryAllChunks(contract.filters.EscrowCreated()),
        queryAllChunks(contract.filters.EscrowReleased())
      ])
      const volume = escrowReleased.reduce((sum, e) => sum + Number(ethers.formatEther(e.args.amount)), 0)
      return json(res, 200, {
        agents: agentCount, volume: parseFloat(volume.toFixed(6)),
        jobs: escrowReleased.length, escrows: escrowCreated.length - escrowReleased.length,
        contract: CONTRACT, block: currentBlock
      })
    } catch (e) { return json(res, 500, { error: e.message }) }
  }

  // GET /api/services
  if (req.method === 'GET' && req.url === '/api/services') {
    try {
      const events = await queryAllChunks(contract.filters.ServiceListed())
      const seen = new Map()
      for (const e of events) {
        const key = `${e.args.agent}-${e.args.serviceType}`
        seen.set(key, { agent: e.args.agent, serviceType: e.args.serviceType,
          price_eth: ethers.formatEther(e.args.price), block: e.blockNumber, tx: e.transactionHash })
      }
      const services = Array.from(seen.values())
      return json(res, 200, { services, total: services.length })
    } catch (e) { return json(res, 500, { error: e.message }) }
  }

  // POST /api/service
  if (req.method === 'POST' && req.url === '/api/service') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', async () => {
      try {
        const { address, serviceType, price_eth } = JSON.parse(body)
        if (!address || !ethers.isAddress(address)) return json(res, 400, { error: 'Invalid address' })
        if (!serviceType) return json(res, 400, { error: 'serviceType required' })
        const info = await contract.agents(address)
        if (!info.registered) return json(res, 400, { error: 'Agent not registered' })
        const priceWei = ethers.parseEther(String(price_eth || '0'))
        const balance = await provider.getBalance(signer.address)
        if (balance < ethers.parseEther('0.00005')) return json(res, 503, { error: 'Gas tank low.' })
        const tx = await contract.listService(serviceType, priceWei)
        await tx.wait()
        return json(res, 200, { success: true, txHash: tx.hash, message: `Service "${serviceType}" listed!` })
      } catch (e) { return json(res, 500, { error: e.message }) }
    })
    return
  }

  // GET /api/bounties
  if (req.method === 'GET' && req.url.startsWith('/api/bounties')) {
    try {
      const events = await queryAllChunks(contract.filters.BountyPosted())
      const bounties = await Promise.all(events.map(async e => {
        const b = await contract.bounties(e.args.id)
        return {
          id: e.args.id, client: b.client,
          provider: b.provider === '0x0000000000000000000000000000000000000000' ? null : b.provider,
          amount_usdc: (Number(b.amount) / 1e6).toFixed(2),
          description: b.description, result: b.result || null,
          status: BOUNTY_STATUS[Number(b.status)],
          block: e.blockNumber, tx: e.transactionHash
        }
      }))
      const status = new URL(req.url, 'http://x').searchParams.get('status')
      const filtered = status ? bounties.filter(b => b.status.toLowerCase() === status.toLowerCase()) : bounties
      return json(res, 200, { bounties: filtered, total: filtered.length })
    } catch (e) { return json(res, 500, { error: e.message }) }
  }

  // POST /api/bounty/claim
  if (req.method === 'POST' && req.url === '/api/bounty/claim') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', async () => {
      try {
        const { bountyId, agentAddress } = JSON.parse(body)
        if (!bountyId) return json(res, 400, { error: 'bountyId required' })
        if (!agentAddress || !ethers.isAddress(agentAddress)) return json(res, 400, { error: 'Invalid agentAddress' })
        const info = await contract.agents(agentAddress)
        if (!info.registered) return json(res, 400, { error: 'Agent not registered' })
        const balance = await provider.getBalance(signer.address)
        if (balance < ethers.parseEther('0.00005')) return json(res, 503, { error: 'Gas tank low.' })
        const tx = await contract.claimBounty(bountyId)
        await tx.wait()
        return json(res, 200, { success: true, txHash: tx.hash, message: 'Bounty claimed!' })
      } catch (e) { return json(res, 500, { error: e.message }) }
    })
    return
  }

  // POST /api/bounty/submit
  if (req.method === 'POST' && req.url === '/api/bounty/submit') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', async () => {
      try {
        const { bountyId, agentAddress, result } = JSON.parse(body)
        if (!bountyId) return json(res, 400, { error: 'bountyId required' })
        if (!result) return json(res, 400, { error: 'result required' })
        const balance = await provider.getBalance(signer.address)
        if (balance < ethers.parseEther('0.00005')) return json(res, 503, { error: 'Gas tank low.' })
        const tx = await contract.submitWork(bountyId, result)
        await tx.wait()
        return json(res, 200, { success: true, txHash: tx.hash, message: 'Work submitted!' })
      } catch (e) { return json(res, 500, { error: e.message }) }
    })
    return
  }

  json(res, 404, { error: 'Not found' })
})

// ── Start ─────────────────────────────────────────────────────────────────────
async function start() {
  await initDB()
  try { await indexAgents() } catch (e) { console.warn('[relayer] indexAgents skipped:', e.message) }
  server.listen(PORT, () => console.log(`[relayer] 🚀 Ready on port ${PORT}`))
}

start()
