#!/usr/bin/env node
/**
 * HYPHA Hyperswarm Bridge
 * P2P discovery and connectivity using Hyperswarm DHT
 * Bridges Python to Node.js Hyperswarm ecosystem
 */

const Hyperswarm = require('hyperswarm');
const crypto = require('crypto');

// Command-line argument parsing
const args = process.argv.slice(2);
const command = args[0]; // 'announce' or 'lookup'
const topic = args[1];

if (!command || !topic) {
  console.error('Usage: node bridge.js <announce|lookup> <topic>');
  process.exit(1);
}

// Create topic hash for DHT
function createTopicHash(topicString) {
  return crypto.createHash('sha256').update(topicString).digest();
}

// Main execution
async function main() {
  const swarm = new Hyperswarm();
  const topicHash = createTopicHash(topic);

  if (command === 'announce') {
    // Announce as provider on the DHT topic
    const discovery = swarm.join(topicHash, { server: true, client: false });

    // Wait for DHT announcement to propagate
    await discovery.flushed();

    console.log(JSON.stringify({
      status: 'announced',
      topic: topic,
      peers: swarm.connections.size
    }));

    // Keep alive for a short time to accept connections
    setTimeout(() => {
      swarm.leave(topicHash);
      swarm.destroy();
      process.exit(0);
    }, 5000);

  } else if (command === 'lookup') {
    // Lookup peers on the DHT topic
    const discovery = swarm.join(topicHash, { server: false, client: true });
    const peers = [];

    // Collect peer connections
    swarm.on('connection', (conn, info) => {
      peers.push({
        publicKey: info.publicKey.toString('hex'),
        host: conn.remoteHost,
        port: conn.remotePort
      });

      // Close connection after collecting info
      conn.destroy();
    });

    // Wait for discovery
    await discovery.flushed();

    // Give some time to discover peers
    setTimeout(() => {
      console.log(JSON.stringify(peers));
      swarm.leave(topicHash);
      swarm.destroy();
      process.exit(0);
    }, 3000);

  } else {
    console.error('Unknown command:', command);
    process.exit(1);
  }
}

// Error handling
process.on('unhandledRejection', (err) => {
  console.error('Error:', err.message);
  process.exit(1);
});

// Run main function
main().catch((err) => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
