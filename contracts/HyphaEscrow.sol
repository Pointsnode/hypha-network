// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title HyphaEscrow
 * @dev USDT escrow contract for autonomous AI agent transactions
 * Enables trustless payments between agents with dispute resolution
 */
contract HyphaEscrow is ReentrancyGuard {

    IERC20 public usdtToken;

    enum EscrowStatus { Active, Completed, Disputed, Refunded, Cancelled }

    struct Escrow {
        address buyer;
        address provider;
        uint256 amount;
        string taskDescription;
        EscrowStatus status;
        uint256 createdAt;
        uint256 deadline;
    }

    // Escrow storage
    mapping(bytes32 => Escrow) public escrows;

    // Events
    event EscrowCreated(
        bytes32 indexed escrowId,
        address indexed buyer,
        address indexed provider,
        uint256 amount,
        string taskDescription
    );

    event EscrowCompleted(
        bytes32 indexed escrowId,
        address indexed provider,
        uint256 amount
    );

    event EscrowRefunded(
        bytes32 indexed escrowId,
        address indexed buyer,
        uint256 amount
    );

    event EscrowDisputed(
        bytes32 indexed escrowId,
        address indexed disputedBy
    );

    /**
     * @dev Constructor sets the USDT token address
     * @param _usdtToken Address of USDT token contract
     */
    constructor(address _usdtToken) {
        require(_usdtToken != address(0), "Invalid USDT address");
        usdtToken = IERC20(_usdtToken);
    }

    /**
     * @dev Create a new escrow
     * @param provider Address of the service provider agent
     * @param amount USDT amount in smallest units (6 decimals)
     * @param taskDescription Description of the task
     * @param deadline Unix timestamp for task deadline
     * @return escrowId Unique identifier for the escrow
     */
    function createEscrow(
        address provider,
        uint256 amount,
        string memory taskDescription,
        uint256 deadline
    ) external nonReentrant returns (bytes32) {
        require(provider != address(0), "Invalid provider address");
        require(provider != msg.sender, "Cannot hire yourself");
        require(amount > 0, "Amount must be greater than 0");
        require(deadline > block.timestamp, "Deadline must be in future");

        // Generate unique escrow ID
        bytes32 escrowId = keccak256(
            abi.encodePacked(
                msg.sender,
                provider,
                amount,
                taskDescription,
                block.timestamp
            )
        );

        require(escrows[escrowId].buyer == address(0), "Escrow already exists");

        // Transfer USDT from buyer to contract
        require(
            usdtToken.transferFrom(msg.sender, address(this), amount),
            "USDT transfer failed"
        );

        // Create escrow
        escrows[escrowId] = Escrow({
            buyer: msg.sender,
            provider: provider,
            amount: amount,
            taskDescription: taskDescription,
            status: EscrowStatus.Active,
            createdAt: block.timestamp,
            deadline: deadline
        });

        emit EscrowCreated(escrowId, msg.sender, provider, amount, taskDescription);

        return escrowId;
    }

    /**
     * @dev Complete escrow and release payment to provider
     * @param escrowId The escrow identifier
     */
    function completeEscrow(bytes32 escrowId) external nonReentrant {
        Escrow storage escrow = escrows[escrowId];

        require(escrow.buyer != address(0), "Escrow does not exist");
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(msg.sender == escrow.buyer, "Only buyer can complete");

        // Update status
        escrow.status = EscrowStatus.Completed;

        // Transfer USDT to provider
        require(
            usdtToken.transfer(escrow.provider, escrow.amount),
            "USDT transfer failed"
        );

        emit EscrowCompleted(escrowId, escrow.provider, escrow.amount);
    }

    /**
     * @dev Provider can auto-complete after deadline if no dispute
     * @param escrowId The escrow identifier
     */
    function claimAfterDeadline(bytes32 escrowId) external nonReentrant {
        Escrow storage escrow = escrows[escrowId];

        require(escrow.buyer != address(0), "Escrow does not exist");
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(msg.sender == escrow.provider, "Only provider can claim");
        require(block.timestamp > escrow.deadline, "Deadline not reached");

        // Update status
        escrow.status = EscrowStatus.Completed;

        // Transfer USDT to provider
        require(
            usdtToken.transfer(escrow.provider, escrow.amount),
            "USDT transfer failed"
        );

        emit EscrowCompleted(escrowId, escrow.provider, escrow.amount);
    }

    /**
     * @dev Dispute an escrow (freezes funds)
     * @param escrowId The escrow identifier
     */
    function disputeEscrow(bytes32 escrowId) external {
        Escrow storage escrow = escrows[escrowId];

        require(escrow.buyer != address(0), "Escrow does not exist");
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(
            msg.sender == escrow.buyer || msg.sender == escrow.provider,
            "Only buyer or provider can dispute"
        );

        escrow.status = EscrowStatus.Disputed;

        emit EscrowDisputed(escrowId, msg.sender);
    }

    /**
     * @dev Refund escrow to buyer (before deadline, mutual agreement)
     * @param escrowId The escrow identifier
     */
    function refundEscrow(bytes32 escrowId) external nonReentrant {
        Escrow storage escrow = escrows[escrowId];

        require(escrow.buyer != address(0), "Escrow does not exist");
        require(escrow.status == EscrowStatus.Active, "Escrow not active");
        require(msg.sender == escrow.provider, "Only provider can refund");

        // Update status
        escrow.status = EscrowStatus.Refunded;

        // Transfer USDT back to buyer
        require(
            usdtToken.transfer(escrow.buyer, escrow.amount),
            "USDT transfer failed"
        );

        emit EscrowRefunded(escrowId, escrow.buyer, escrow.amount);
    }

    /**
     * @dev Get escrow details
     * @param escrowId The escrow identifier
     */
    function getEscrow(bytes32 escrowId) external view returns (
        address buyer,
        address provider,
        uint256 amount,
        string memory taskDescription,
        EscrowStatus status,
        uint256 createdAt,
        uint256 deadline
    ) {
        Escrow memory escrow = escrows[escrowId];
        return (
            escrow.buyer,
            escrow.provider,
            escrow.amount,
            escrow.taskDescription,
            escrow.status,
            escrow.createdAt,
            escrow.deadline
        );
    }
}
