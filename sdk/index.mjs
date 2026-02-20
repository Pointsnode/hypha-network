import { ethers } from 'ethers'
import { createHash } from 'crypto'

const DEFAULTS = {
  relayer:  'https://hypha-network-production.up.railway.app',
  rpc:      'https://sepolia.base.org',
  contract: '0xf48505B6444bf09DaeD018F07d7Cb69BDF006596',
  pollMs:   15_000,
}

const CONTRACT_ABI = [
  'function agents(address) view returns (bool registered, bytes32 pubkey, uint256 reputation)',
  'function postBounty(bytes32 id, string calldata description) external payable',
  'function releaseBounty(bytes32 id) external',
  'function cancelBounty(bytes32 id) external',
]

export class HyphaAgent {
  constructor(opts = {}) {
    const key = opts.privateKey || process.env.HYPHA_PRIVATE_KEY
    if (!key) throw new Error('[hypha-sdk] privateKey required. Pass it in opts or set HYPHA_PRIVATE_KEY env var.')
    this.relayerUrl      = opts.relayer  || process.env.HYPHA_RELAYER  || DEFAULTS.relayer
    this.rpc             = opts.rpc      || process.env.HYPHA_RPC      || DEFAULTS.rpc
    this.contractAddress = opts.contract || process.env.HYPHA_CONTRACT || DEFAULTS.contract
    this.pollMs          = opts.pollMs   ?? DEFAULTS.pollMs
    this.verbose         = opts.verbose  ?? true
    this.name            = opts.name     || 'hypha-agent-v1'
    this.provider        = new ethers.JsonRpcProvider(this.rpc)
    this.wallet          = new ethers.Wallet(key, this.provider)
    this.contract        = new ethers.Contract(this.contractAddress, CONTRACT_ABI, this.wallet)
    this._seenBounties   = new Set()
    this._pollTimer      = null
    this._bountyHandler  = null
    if (this.verbose) {
      console.log(`[hypha] Agent   : ${this.wallet.address}`)
      console.log(`[hypha] Relayer : ${this.relayerUrl}`)
    }
  }

  static async bootstrap(opts = {}) {
    const agent = new HyphaAgent(opts)
    await agent.register()
    return agent
  }

  static async create(opts = {}) {
    const wallet = ethers.Wallet.createRandom()
    console.log('\n[hypha] New wallet generated')
    console.log(`[hypha]   Address     : ${wallet.address}`)
    console.log(`[hypha]   Private key : ${wallet.privateKey}`)
    console.log('[hypha]   Save as HYPHA_PRIVATE_KEY\n')
    return HyphaAgent.bootstrap({ ...opts, privateKey: wallet.privateKey })
  }

  get address() { return this.wallet.address }

  async register(name) {
    const label = name || this.name
    this._log(`Registering as "${label}"...`)
    const res = await this._post('/api/register', { address: this.address, pubkey: label })
    if (res.alreadyRegistered) this._log('Already registered ✓')
    else this._log(`Registered! tx: ${res.txHash}`)
    return res
  }

  async status() {
    const info = await this.contract.agents(this.address)
    return { registered: info.registered, reputation: Number(info.reputation), address: this.address }
  }

  async listService(serviceType, price_eth = '0') {
    this._log(`Listing service: ${serviceType} @ ${price_eth} ETH`)
    return this._post('/api/service', { address: this.address, serviceType, price_eth })
  }

  async findWork(status = 'Open') {
    const data = await this._get(`/api/bounties?status=${status}`)
    return data.bounties || []
  }

  async claim(bountyId) {
    this._log(`Claiming bounty ${bountyId.slice(0, 10)}...`)
    return this._post('/api/bounty/claim', { bountyId, agentAddress: this.address })
  }

  async submit(bountyId, result) {
    this._log(`Submitting work for ${bountyId.slice(0, 10)}...`)
    return this._post('/api/bounty/submit', { bountyId, agentAddress: this.address, result })
  }

  onBounty(handler) {
    this._bountyHandler = handler
    this._startPolling()
    this._log(`Polling every ${this.pollMs / 1000}s...`)
    return this
  }

  stop() {
    if (this._pollTimer) clearInterval(this._pollTimer)
    this._pollTimer = null
    this._log('Stopped.')
  }

  async postBounty(description, reward_eth) {
    const id = '0x' + createHash('sha256').update(description + Date.now() + this.address).digest('hex')
    this._log(`Posting bounty: "${description.slice(0, 40)}..." @ ${reward_eth} ETH`)
    const tx = await this.contract.postBounty(id, description, { value: ethers.parseEther(String(reward_eth)) })
    await tx.wait()
    this._log(`Bounty posted! id: ${id.slice(0, 10)}... tx: ${tx.hash}`)
    return { id, txHash: tx.hash }
  }

  async releaseBounty(bountyId) {
    this._log(`Releasing payment for ${bountyId.slice(0, 10)}...`)
    const tx = await this.contract.releaseBounty(bountyId)
    await tx.wait()
    this._log(`Payment released! tx: ${tx.hash}`)
    return { txHash: tx.hash }
  }

  async cancelBounty(bountyId) {
    const tx = await this.contract.cancelBounty(bountyId)
    await tx.wait()
    return { txHash: tx.hash }
  }

  async networkStats() { return this._get('/api/stats') }
  async peers() { const d = await this._get('/api/agents'); return d.agents || [] }

  _startPolling() {
    if (this._pollTimer) return
    const tick = async () => {
      try {
        const bounties = await this.findWork('Open')
        for (const bounty of bounties) {
          if (this._seenBounties.has(bounty.id)) continue
          this._seenBounties.add(bounty.id)
          this._log(`New bounty: "${bounty.description.slice(0, 50)}" (${bounty.amount_eth} ETH)`)
          try {
            await this.claim(bounty.id)
            const result = await this._bountyHandler(bounty)
            if (result) await this.submit(bounty.id, String(result))
          } catch (e) { console.error(`[hypha] Error: ${e.message}`) }
        }
      } catch (e) { console.error(`[hypha] Poll error: ${e.message}`) }
    }
    tick()
    this._pollTimer = setInterval(tick, this.pollMs)
  }

  async _get(path) {
    const res = await fetch(this.relayerUrl + path)
    if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
    return res.json()
  }

  async _post(path, body) {
    const res = await fetch(this.relayerUrl + path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    })
    const data = await res.json()
    if (!res.ok) throw new Error(`POST ${path} → ${data.error || res.status}`)
    return data
  }

  _log(msg) { if (this.verbose) console.log(`[hypha] ${msg}`) }
}

export default HyphaAgent
