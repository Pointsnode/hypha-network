/**
 * HYPHA Escrow Deployment Script
 * Deploys HyphaEscrow contract to Base Sepolia or Base Mainnet
 */

const hre = require("hardhat");

// USDT Contract Addresses
const USDT_ADDRESSES = {
  baseSepolia: "0x036CbD53842c5426634e7929541eC2318f3dCF7e", // Base Sepolia USDC (test token)
  base: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", // USDC on Base (as proxy for USDT)
  hardhat: "0x0000000000000000000000000000000000000000" // Mock for local testing
};

async function main() {
  const network = hre.network.name;
  console.log(`\n🚀 Deploying HyphaEscrow to ${network}...`);

  // Get USDT address for network
  const usdtAddress = USDT_ADDRESSES[network];

  if (!usdtAddress || usdtAddress === "0x") {
    console.error(`❌ No USDT address configured for ${network}`);
    console.log("Please update USDT_ADDRESSES in deploy.js");
    process.exit(1);
  }

  console.log(`📍 USDT Token Address: ${usdtAddress}`);

  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log(`👤 Deploying with account: ${deployer.address}`);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log(`💰 Account balance: ${hre.ethers.formatEther(balance)} ETH`);

  // Deploy contract
  const HyphaEscrow = await hre.ethers.getContractFactory("HyphaEscrow");
  const escrow = await HyphaEscrow.deploy(usdtAddress);

  await escrow.waitForDeployment();

  const escrowAddress = await escrow.getAddress();
  console.log(`\n✅ HyphaEscrow deployed to: ${escrowAddress}`);

  // Save deployment info
  const deploymentInfo = {
    network: network,
    escrowContract: escrowAddress,
    usdtToken: usdtAddress,
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber()
  };

  console.log("\n📝 Deployment Info:");
  console.log(JSON.stringify(deploymentInfo, null, 2));

  // Verification instructions
  if (network !== "hardhat") {
    console.log("\n🔍 To verify contract on Basescan:");
    console.log(`npx hardhat verify --network ${network} ${escrowAddress} ${usdtAddress}`);
  }

  console.log("\n✨ Next steps:");
  console.log("1. Update .env with ESCROW_CONTRACT_ADDRESS=" + escrowAddress);
  console.log("2. Update .env with USDT_CONTRACT_ADDRESS=" + usdtAddress);
  console.log("3. Test escrow with: npm run test:escrow");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
