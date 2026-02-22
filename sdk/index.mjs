import { ethers } from 'ethers'
import { createHash } from 'crypto'

const DEFAULTS = {
  relayer:  'https://hypha-network-production.up.railway.app',
  rpc:      'https://mainnet.base.org',
  contract: '0xf1cF5A40ad2c48456C2aD4d59554Ad9baa51F644',
  usdc:     '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
  pollMs:   15_000,
}

const CONTRACT_ABI = [
  'function agents(address) view returns (bool registered, bytes32 pubkey, uint256 reputation)',
  'function postBounty(bytes32 id, string calldata description, uint256 amount) external',
  'function releaseBounty(bytes32 id) external',
  'function cancelBounty(bytes32 id) external',
  'event BountyPosted(bytes32 indexed id, address indexed client, uint256 amount, string description)',
]

const ERC20_ABI = [
  'function approve(address spender, uint256 amount) external returns (bool)',
  'function allowance(address owner, address spender) view returns (uint256)',
  'function balanceOf(address account) view returns (uint256)',
]

export class HyphaAgent {
  constructor(opts = {}) {
    const key = opts.privateKey || process.env.HYPHA_PRIVATE_KEY
    if (!key) throw new Error('[hypha-sdk] privateKey required.')
    this.relayerUrl      = opts.relayer  || process.env.HYPHA_RELAYER   || DEFAULTS.relayer
    this.rpc             = opts.rpc      || process.env.HYPHA_RPC        || DEFAULTS.rpc
    this.contractAddress = opts.contract || process.env.HYPHA_CONTRACT   || DEFAULTS.contract
    this.usdcAddress     = opts.usdc     || DEFAULTS.usdc
    this.pollMs          = opts.pollMs   ?? DEFAULTS.pollMs
    this.verbose         = opts.verbose  ?? true
    this.name            = opts.name     || 'hypha-agent-v1'
    this.provider = new ethers.JsonRpcProvider(this.rpc)
    this.wallet   = new ethers.Wallet(key, this.provider)
    this.contract = new ethers.Contract(this.contractAddress, CONTRACT_ABI, this.wallet)
    this.usdc     = new ethers.Contract(this.usdcAddress, ERC20_ABI, this.wallet)
    this._seenBounties = new Set()
    this._pollTimer    = null
    this._bountyHandler = null
    if (this.verbose) {
      console.log(`[hypha] Agent address : ${this.wallet.address}`)
      console.log(`[hypha] Relayer       : ${this.relayerUrl}`)
      console.log(`[hypha] Contract      : ${this.contractAddress}`)
    }
  }
  static async bootstrap(opts = {}) { const a = new HyphaAgent(opts); await a.register(); return a }
  static async create(opts = {}) {
    const w = ethers.Wallet.createRandom()
    console.log('\n[hypha] New wallet:', w.address)
    console.log('[hypha] Private key:', w.privateKey)
    return HyphaAgent.bootstrap({ ...opts, privateKey: w.privateKey })
  }
  get address() { return this.wallet.address }
  async register(name) {
    const label = name || this.name
    this._log(`Registering as "${label}"...`)
    const res = await this._post('/api/register', { address: this.address, pubkey: label })
    this._log(res.alreadyRegistered ? 'Already registered ✓' : `Registered! tx: ${res.txHash}`)
    return res
  }
  async status() {
    const info = await this.contract.agents(this.address)
    return { registered: info.registered, reputation: Number(info.reputation), address: this.address }
  }
  async listService(serviceType, price_usdc = '0') {
    this._log(`Listing service: ${serviceType} @ ${price_usdc} USDC`)
    return this._post('/api/service', { address: this.address, serviceType, price_eth: price_usdc })
  }
  async findWork(status = 'Open') { return (await this._get(`/api/bounties?status=${status}`)).bounties || [] }
  async claim(bountyId) { return this._post('/api/bounty/claim', { bountyId, agentAddress: this.address }) }
  async submit(bountyId, result) { return this._post('/api/bounty/submit', { bountyId, agentAddress: this.address, result }) }
  onBounty(handler) { this._bountyHandler = handler; this._startPolling(); return this }
  stop() { if (this._pollTimer) clearInterval(this._pollTimer); this._pollTimer = null }
  async postBounty(description, reward_usdc) {
    const id = '0x' + createHash('sha256').update(description + Date.now() + this.address).digest('hex')
    const amount = ethers.parseUnits(String(reward_usdc), 6)
    this._log(`Approving ${reward_usdc} USDC...`)
    await (await this.usdc.approve(this.contractAddress, amount)).wait()
    this._log(`Posting bounty: "${description.slice(0,40)}..."`)
    const tx = await this.contract.postBounty(id, description, amount)
    await tx.wait()
    this._log(`Bounty posted! tx: ${tx.hash}`)
    return { id, txHash: tx.hash }
  }
  async releaseBounty(bountyId) { const tx = await this.contract.releaseBounty(bountyId); await tx.wait(); return { txHash: tx.hash } }
  async cancelBounty(bountyId)  { const tx = await this.contract.cancelBounty(bountyId);  await tx.wait(); return { txHash: tx.hash } }
  async networkStats() { return this._get('/api/stats') }
  async peers() { return (await this._get('/api/agents')).agents || [] }
  _startPolling() {
    if (this._pollTimer) return
    const tick = async () => {
      try {
        for (const b of await this.findWork('Open')) {
          if (this._seenBounties.has(b.id)) continue
          this._seenBounties.add(b.id)
          this._log(`New bounty: "${b.description.slice(0,50)}" ($${b.amount_usdc||'?'} USDC)`)
          try { await this.claim(b.id); const r = await this._bountyHandler(b); if (r) await this.submit(b.id, String(r)) }
          catch(e) { console.error('[hypha] Error:', e.message) }
        }
      } catch(e) { console.error('[hypha] Poll error:', e.message) }
    }
    tick()
    this._pollTimer = setInterval(tick, this.pollMs)
  }
  async _get(path) { const r = await fetch(this.relayerUrl+path); if(!r.ok) throw new Error(`GET ${path} → ${r.status}`); return r.json() }
  async _post(path, body) {
    const r = await fetch(this.relayerUrl+path, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) })
    const d = await r.json(); if(!r.ok) throw new Error(d.error||r.status); return d
  }
  _log(msg) { if (this.verbose) console.log(`[hypha] ${msg}`) }
}
export default HyphaAgent
