#!/usr/bin/env node
/**
 * HYPHA Message Send Bridge
 * Sends messages to peers via Hyperswarm
 */

const Hyperswarm = require('hyperswarm');
const crypto = require('crypto');

// Parse arguments
const args = process.argv.slice(2);
const topic = args[0];
const messageJson = args[1];

if (!topic || !messageJson) {
  console.error('Usage: node send_bridge.js <topic> <message_json>');
  process.exit(1);
}

// Create topic hash
function createTopicHash(topicString) {
  return crypto.createHash('sha256').update(topicString).digest();
}

async function sendMessage() {
  const swarm = new Hyperswarm();
  const topicHash = createTopicHash(topic);

  let messageSent = false;

  // Join as client to find providers
  swarm.join(topicHash, { server: false, client: true });

  // When connected to a peer, send the message
  swarm.on('connection', (conn, info) => {
    // Send message
    conn.write(messageJson);
    messageSent = true;

    // Close after sending
    setTimeout(() => {
      conn.destroy();
    }, 100);
  });

  // Wait for message to be sent
  await new Promise((resolve) => {
    setTimeout(() => {
      if (messageSent) {
        console.log(JSON.stringify({ status: 'sent', topic }));
        process.exit(0);
      } else {
        console.error(JSON.stringify({ status: 'failed', topic, error: 'No peers found' }));
        process.exit(1);
      }
    }, 5000);
  });
}

// Error handling
process.on('unhandledRejection', (err) => {
  console.error(JSON.stringify({ status: 'error', message: err.message }));
  process.exit(1);
});

sendMessage().catch((err) => {
  console.error(JSON.stringify({ status: 'error', message: err.message }));
  process.exit(1);
});
