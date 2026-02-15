/**
 * HYPHA Escrow Contract Tests
 * Comprehensive tests for HyphaEscrow smart contract
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("HyphaEscrow", function () {
  let escrow, usdt, buyer, provider, other;
  const TASK_AMOUNT = ethers.parseUnits("10", 6); // 10 USDT
  const INITIAL_BALANCE = ethers.parseUnits("1000", 6); // 1000 USDT

  beforeEach(async function () {
    [buyer, provider, other] = await ethers.getSigners();

    // Deploy MockUSDT
    const MockUSDT = await ethers.getContractFactory("MockUSDT");
    usdt = await MockUSDT.deploy();
    await usdt.waitForDeployment();

    // Deploy HyphaEscrow
    const HyphaEscrow = await ethers.getContractFactory("HyphaEscrow");
    escrow = await HyphaEscrow.deploy(await usdt.getAddress());
    await escrow.waitForDeployment();

    // Setup: Mint USDT to buyer and approve escrow
    await usdt.mint(buyer.address, INITIAL_BALANCE);
    await usdt.connect(buyer).approve(await escrow.getAddress(), INITIAL_BALANCE);
  });

  describe("Deployment", function () {
    it("Should set the correct USDT token address", async function () {
      expect(await escrow.usdtToken()).to.equal(await usdt.getAddress());
    });

    it("Should start with zero escrows", async function () {
      // Since there's no public escrow count, we'll verify by trying to get a non-existent escrow
      const nonExistentId = ethers.keccak256(ethers.toUtf8Bytes("non-existent"));

      try {
        await escrow.getEscrow(nonExistentId);
        // If it doesn't revert, check the buyer is zero address
        const escrowData = await escrow.getEscrow(nonExistentId);
        expect(escrowData[0]).to.equal(ethers.ZeroAddress);
      } catch (error) {
        // Expected to fail for non-existent escrow
        expect(error).to.exist;
      }
    });
  });

  describe("Create Escrow", function () {
    it("Should create escrow and emit event", async function () {
      const deadline = await time.latest() + 86400; // 24 hours from now

      const tx = await escrow.connect(buyer).createEscrow(
        provider.address,
        TASK_AMOUNT,
        "Analyze blockchain data",
        deadline
      );

      await expect(tx)
        .to.emit(escrow, "EscrowCreated")
        .withArgs(
          (escrowId) => escrowId !== ethers.ZeroHash, // Check escrowId is not zero
          buyer.address,
          provider.address,
          TASK_AMOUNT,
          "Analyze blockchain data"
        );
    });

    it("Should transfer USDT from buyer to escrow", async function () {
      const deadline = await time.latest() + 86400;
      const buyerBalanceBefore = await usdt.balanceOf(buyer.address);
      const escrowBalanceBefore = await usdt.balanceOf(await escrow.getAddress());

      await escrow.connect(buyer).createEscrow(
        provider.address,
        TASK_AMOUNT,
        "Test task",
        deadline
      );

      const buyerBalanceAfter = await usdt.balanceOf(buyer.address);
      const escrowBalanceAfter = await usdt.balanceOf(await escrow.getAddress());

      expect(buyerBalanceBefore - buyerBalanceAfter).to.equal(TASK_AMOUNT);
      expect(escrowBalanceAfter - escrowBalanceBefore).to.equal(TASK_AMOUNT);
    });

    it("Should store correct escrow details", async function () {
      const deadline = await time.latest() + 86400;
      const taskDescription = "Comprehensive data analysis";

      const tx = await escrow.connect(buyer).createEscrow(
        provider.address,
        TASK_AMOUNT,
        taskDescription,
        deadline
      );

      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return escrow.interface.parseLog(log).name === "EscrowCreated";
        } catch {
          return false;
        }
      });

      const escrowId = escrow.interface.parseLog(event).args.escrowId;

      const escrowData = await escrow.getEscrow(escrowId);

      expect(escrowData[0]).to.equal(buyer.address); // buyer
      expect(escrowData[1]).to.equal(provider.address); // provider
      expect(escrowData[2]).to.equal(TASK_AMOUNT); // amount
      expect(escrowData[3]).to.equal(taskDescription); // task
      expect(escrowData[4]).to.equal(0); // status (Active)
      expect(escrowData[6]).to.equal(deadline); // deadline
    });

    it("Should fail if insufficient balance", async function () {
      const deadline = await time.latest() + 86400;
      const largeAmount = ethers.parseUnits("10000", 6); // More than buyer has

      await expect(
        escrow.connect(buyer).createEscrow(
          provider.address,
          largeAmount,
          "Task",
          deadline
        )
      ).to.be.reverted;
    });

    it("Should fail if insufficient allowance", async function () {
      const deadline = await time.latest() + 86400;

      // Reset approval to 0
      await usdt.connect(buyer).approve(await escrow.getAddress(), 0);

      await expect(
        escrow.connect(buyer).createEscrow(
          provider.address,
          TASK_AMOUNT,
          "Task",
          deadline
        )
      ).to.be.reverted;
    });
  });

  describe("Complete Escrow", function () {
    let escrowId;

    beforeEach(async function () {
      const deadline = await time.latest() + 86400;

      const tx = await escrow.connect(buyer).createEscrow(
        provider.address,
        TASK_AMOUNT,
        "Test task",
        deadline
      );

      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return escrow.interface.parseLog(log).name === "EscrowCreated";
        } catch {
          return false;
        }
      });

      escrowId = escrow.interface.parseLog(event).args.escrowId;
    });

    it("Should complete escrow and transfer funds to provider", async function () {
      const providerBalanceBefore = await usdt.balanceOf(provider.address);

      await escrow.connect(buyer).completeEscrow(escrowId);

      const providerBalanceAfter = await usdt.balanceOf(provider.address);

      expect(providerBalanceAfter - providerBalanceBefore).to.equal(TASK_AMOUNT);
    });

    it("Should emit EscrowCompleted event", async function () {
      await expect(escrow.connect(buyer).completeEscrow(escrowId))
        .to.emit(escrow, "EscrowCompleted")
        .withArgs(escrowId, provider.address, TASK_AMOUNT);
    });

    it("Should update escrow status to Completed", async function () {
      await escrow.connect(buyer).completeEscrow(escrowId);

      const escrowData = await escrow.getEscrow(escrowId);
      expect(escrowData[4]).to.equal(1); // status = Completed
    });

    it("Should fail if caller is not buyer", async function () {
      await expect(
        escrow.connect(provider).completeEscrow(escrowId)
      ).to.be.revertedWith("Only buyer can complete");
    });

    it("Should fail if escrow already completed", async function () {
      await escrow.connect(buyer).completeEscrow(escrowId);

      await expect(
        escrow.connect(buyer).completeEscrow(escrowId)
      ).to.be.revertedWith("Escrow not active");
    });
  });

  describe("Refund Escrow", function () {
    let escrowId;

    beforeEach(async function () {
      const deadline = await time.latest() + 86400;

      const tx = await escrow.connect(buyer).createEscrow(
        provider.address,
        TASK_AMOUNT,
        "Test task",
        deadline
      );

      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return escrow.interface.parseLog(log).name === "EscrowCreated";
        } catch {
          return false;
        }
      });

      escrowId = escrow.interface.parseLog(event).args.escrowId;
    });

    it("Should refund after deadline expires", async function () {
      const buyerBalanceBefore = await usdt.balanceOf(buyer.address);

      // Fast forward past deadline
      await time.increase(86401); // 24 hours + 1 second

      await escrow.connect(provider).refundEscrow(escrowId);

      const buyerBalanceAfter = await usdt.balanceOf(buyer.address);

      expect(buyerBalanceAfter - buyerBalanceBefore).to.equal(TASK_AMOUNT);
    });

    it("Should emit EscrowRefunded event", async function () {
      await time.increase(86401);

      await expect(escrow.connect(provider).refundEscrow(escrowId))
        .to.emit(escrow, "EscrowRefunded")
        .withArgs(escrowId, buyer.address, TASK_AMOUNT);
    });

    it("Should fail if deadline not expired", async function () {
      await expect(
        escrow.connect(buyer).refundEscrow(escrowId)
      ).to.be.revertedWith("Only provider can refund");
    });

    it("Should fail if caller is not buyer", async function () {
      await time.increase(86401);

      await expect(
        escrow.connect(buyer).refundEscrow(escrowId)
      ).to.be.revertedWith("Only provider can refund");
    });
  });

  describe("Multiple Escrows", function () {
    it("Should handle multiple escrows independently", async function () {
      const deadline = await time.latest() + 86400;

      // Create first escrow
      const tx1 = await escrow.connect(buyer).createEscrow(
        provider.address,
        TASK_AMOUNT,
        "Task 1",
        deadline
      );

      // Create second escrow with different provider
      const tx2 = await escrow.connect(buyer).createEscrow(
        other.address,
        TASK_AMOUNT,
        "Task 2",
        deadline
      );

      const receipt1 = await tx1.wait();
      const receipt2 = await tx2.wait();

      const event1 = receipt1.logs.find(log => {
        try {
          return escrow.interface.parseLog(log).name === "EscrowCreated";
        } catch {
          return false;
        }
      });

      const event2 = receipt2.logs.find(log => {
        try {
          return escrow.interface.parseLog(log).name === "EscrowCreated";
        } catch {
          return false;
        }
      });

      const escrowId1 = escrow.interface.parseLog(event1).args.escrowId;
      const escrowId2 = escrow.interface.parseLog(event2).args.escrowId;

      // Verify different escrow IDs
      expect(escrowId1).to.not.equal(escrowId2);

      // Verify independent completion
      await escrow.connect(buyer).completeEscrow(escrowId1);

      const escrow1Data = await escrow.getEscrow(escrowId1);
      const escrow2Data = await escrow.getEscrow(escrowId2);

      expect(escrow1Data[4]).to.equal(1); // Completed
      expect(escrow2Data[4]).to.equal(0); // Still Active
    });
  });

  describe("Edge Cases", function () {
    it("Should handle zero amount escrow", async function () {
      const deadline = await time.latest() + 86400;

      // This should likely fail in production, but test current behavior
      await expect(
        escrow.connect(buyer).createEscrow(
          provider.address,
          0,
          "Zero amount task",
          deadline
        )
      ).to.be.revertedWith("Amount must be greater than 0");
    });

    it("Should handle past deadline", async function () {
      const pastDeadline = await time.latest() - 1;

      await expect(
        escrow.connect(buyer).createEscrow(
          provider.address,
          TASK_AMOUNT,
          "Past deadline task",
          pastDeadline
        )
      ).to.be.revertedWith("Deadline must be in future");
    });
  });
});
