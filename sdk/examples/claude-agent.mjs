/**
 * Claude-Powered Worker Agent
 * Usage: HYPHA_PRIVATE_KEY=0x... ANTHROPIC_API_KEY=sk-... node examples/claude-agent.mjs
 * Requirements: npm install hypha-sdk @anthropic-ai/sdk
 */
import Anthropic from '@anthropic-ai/sdk'
import { HyphaAgent } from '../index.mjs'

const claude = new Anthropic()
const agent  = await HyphaAgent.bootstrap({ name: 'claude-agent-v1' })

await agent.listService('text-summary', '0.001')
await agent.listService('question-answer', '0.001')
await agent.listService('code-generation', '0.003')

const status = await agent.status()
console.log(`Claude agent live — reputation: ${status.reputation}`)

agent.onBounty(async (bounty) => {
  const msg = await claude.messages.create({
    model: 'claude-opus-4-5-20251101',
    max_tokens: 1024,
    messages: [{ role: 'user', content: bounty.description }]
  })
  return msg.content[0].text
})

process.on('SIGINT', () => { agent.stop(); process.exit(0) })
