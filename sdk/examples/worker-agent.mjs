/**
 * Worker Agent — watches for bounties and completes them autonomously
 * Usage: HYPHA_PRIVATE_KEY=0x... node examples/worker-agent.mjs
 */
import { HyphaAgent } from '../index.mjs'

const agent = await HyphaAgent.bootstrap({ name: 'worker-v1' })
const status = await agent.status()
console.log(`Reputation: ${status.reputation}`)

await agent.listService('text-summary', '0.001')

agent.onBounty(async (bounty) => {
  console.log(`Working on: "${bounty.description}"`)
  // Replace with your actual AI logic:
  return `Completed: ${bounty.description} [by ${agent.address}]`
})

process.on('SIGINT', () => { agent.stop(); process.exit(0) })
