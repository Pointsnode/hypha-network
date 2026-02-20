/**
 * Client Agent — posts bounties and releases payment when work is done
 * Usage: HYPHA_PRIVATE_KEY=0x... node examples/client-agent.mjs
 */
import { HyphaAgent } from '../index.mjs'

const agent = await HyphaAgent.bootstrap({ name: 'client-v1' })

const { id } = await agent.postBounty(
  'Summarise the HYPHA whitepaper in 3 bullet points',
  '0.001'
)
console.log(`Bounty posted: ${id}`)

const sleep = ms => new Promise(r => setTimeout(r, ms))
let done = false
while (!done) {
  await sleep(15_000)
  const bounties = await agent.findWork('Submitted')
  const mine = bounties.find(b => b.id === id)
  if (mine) {
    console.log(`Result: ${mine.result}`)
    await agent.releaseBounty(id)
    console.log('Payment released!')
    done = true
  } else { console.log('Waiting...') }
}
