#!/usr/bin/env node
/**
 * HYPHA Message Receive Bridge
 * Receives messages from peers via Hyperswarm
 */

const Hyperswarm = require('hyperswarm');
const crypto = require('crypto');

// Parse arguments
const args = process.argv.slice(2);
const topic = args[0];

if (!topic) {
  console.error('Usage: node receive_bridge.js <topic>');
  process.exit(1);
}

// Create topic hash
function createTopicHash(topicString) {
  return crypto.createHash('sha256').update(topicString).digest();
}

async function receiveMessage() {
  const swarm = new Hyperswarm();
  const topicHash = createTopicHash(topic);

  let messageReceived = false;

  // Join as server to receive messages
  swarm.join(topicHash, { server: true, client: false });

  // Listen for incoming connections
  swarm.on('connection', (conn, info) => {
    let dataBuffer = '';

    conn.on('data', (data) => {
      dataBuffer += data.toString();
    });

    conn.on('end', () => {
      if (dataBuffer && !messageReceived) {
        messageReceived = true;
        console.log(dataBuffer); // Output the received message
        swarm.destroy();
        process.exit(0);
      }
    });

    // Also handle connection close
    conn.on('close', () => {
      if (dataBuffer && !messageReceived) {
        messageReceived = true;
        console.log(dataBuffer);
        swarm.destroy();
        process.exit(0);
      }
    });
  });

  // Timeout after 30 seconds
  setTimeout(() => {
    if (!messageReceived) {
      swarm.destroy();
      process.exit(1); // No message received
    }
  }, 30000);
}

// Error handling
process.on('unhandledRejection', (err) => {
  console.error(JSON.stringify({ error: err.message }));
  process.exit(1);
});

receiveMessage().catch((err) => {
  console.error(JSON.stringify({ error: err.message }));
  process.exit(1);
});
