// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract HyphaNetwork {

    // ── Config ───────────────────────────────────────────────────────────
    IERC20  public immutable usdc;
    address public           treasury;
    address public           owner;
    uint256 public constant  FEE_BPS       = 50;   // 0.5% (50 basis points)
    uint256 public constant  MIN_BOUNTY    = 1e6;  // 1 USDC (6 decimals)

    // ── Structs ──────────────────────────────────────────────────────────
    struct Agent {
        bool    registered;
        bytes32 pubkey;
        uint256 reputation;
    }

    struct Service {
        address agent;
        string  serviceType;
        uint256 price;      // in USDC (6 decimals)
        bool    active;
    }

    enum BountyStatus { Open, Claimed, Submitted, Released, Cancelled }

    struct Bounty {
        address       client;
        address       provider;
        uint256       amount;       // in USDC (6 decimals)
        string        description;
        string        result;
        BountyStatus  status;
    }

    struct Escrow {
        address client;
        address provider;
        uint256 amount;     // in USDC (6 decimals)
        bool    released;
        bool    refunded;
    }

    // ── State ────────────────────────────────────────────────────────────
    mapping(address  => Agent)   public agents;
    mapping(bytes32  => Service) public services;
    mapping(bytes32  => Bounty)  public bounties;
    mapping(bytes32  => Escrow)  public escrows;

    // ── Events ───────────────────────────────────────────────────────────
    event AgentRegistered (address indexed agent, bytes32 pubkey);
    event ServiceListed   (address indexed agent, string serviceType, uint256 price);
    event BountyPosted    (bytes32 indexed id, address indexed client, uint256 amount, string description);
    event BountyClaimed   (bytes32 indexed id, address indexed provider);
    event WorkSubmitted   (bytes32 indexed id, address indexed provider, string result);
    event BountyReleased  (bytes32 indexed id, address indexed provider, uint256 amount);
    event BountyCancelled (bytes32 indexed id);
    event EscrowCreated   (bytes32 indexed taskId, address client, address provider, uint256 amount);
    event EscrowReleased  (bytes32 indexed taskId, uint256 amount);
    event EscrowRefunded  (bytes32 indexed taskId, uint256 amount);
    event ReputationUpdated(address indexed agent, uint256 score);

    // ── Modifiers ────────────────────────────────────────────────────────
    modifier onlyOwner()           { require(msg.sender == owner, "Not owner"); _; }
    modifier onlyRegistered()      { require(agents[msg.sender].registered, "Not registered"); _; }

    // ── Constructor ──────────────────────────────────────────────────────
    constructor(address _usdc, address _treasury) {
        usdc     = IERC20(_usdc);
        treasury = _treasury;
        owner    = msg.sender;
    }

    // ── Agent Registration ───────────────────────────────────────────────
    function registerAgent(bytes32 pubkey) external {
        _registerAgent(msg.sender, pubkey);
    }

    function registerAgentFor(address agent, bytes32 pubkey) external {
        _registerAgent(agent, pubkey);
    }

    function _registerAgent(address agent, bytes32 pubkey) internal {
        require(!agents[agent].registered, "Already registered");
        agents[agent] = Agent({ registered: true, pubkey: pubkey, reputation: 0 });
        emit AgentRegistered(agent, pubkey);
    }

    // ── Services ─────────────────────────────────────────────────────────
    function listService(string calldata serviceType, uint256 price) external onlyRegistered {
        bytes32 id = keccak256(abi.encodePacked(msg.sender, serviceType));
        services[id] = Service({ agent: msg.sender, serviceType: serviceType, price: price, active: true });
        emit ServiceListed(msg.sender, serviceType, price);
    }

    // ── Bounty Marketplace ───────────────────────────────────────────────

    /// @notice Post a bounty. Client must approve USDC spend first.
    /// @param id          Unique bounty ID (use keccak256 of description+nonce)
    /// @param description Task description for agents
    /// @param amount      Reward in USDC (minimum 1 USDC = 1_000_000)
    function postBounty(bytes32 id, string calldata description, uint256 amount) external {
        require(bounties[id].client == address(0), "Bounty ID already used");
        require(amount >= MIN_BOUNTY, "Minimum bounty is 1 USDC");
        require(usdc.transferFrom(msg.sender, address(this), amount), "USDC transfer failed");

        bounties[id] = Bounty({
            client:      msg.sender,
            provider:    address(0),
            amount:      amount,
            description: description,
            result:      "",
            status:      BountyStatus.Open
        });
        emit BountyPosted(id, msg.sender, amount, description);
    }

    /// @notice Claim an open bounty (registered agents only)
    function claimBounty(bytes32 id) external onlyRegistered {
        Bounty storage b = bounties[id];
        require(b.status == BountyStatus.Open, "Bounty not open");
        require(b.client != msg.sender, "Cannot claim own bounty");
        b.provider = msg.sender;
        b.status   = BountyStatus.Claimed;
        emit BountyClaimed(id, msg.sender);
    }

    /// @notice Submit completed work
    function submitWork(bytes32 id, string calldata result) external {
        Bounty storage b = bounties[id];
        require(b.status == BountyStatus.Claimed, "Bounty not claimed");
        require(b.provider == msg.sender, "Not the provider");
        b.result = result;
        b.status = BountyStatus.Submitted;
        emit WorkSubmitted(id, msg.sender, result);
    }

    /// @notice Client approves work and releases USDC to agent (minus 0.5% fee)
    function releaseBounty(bytes32 id) external {
        Bounty storage b = bounties[id];
        require(b.status == BountyStatus.Submitted, "Work not submitted");
        require(b.client == msg.sender, "Not the client");

        uint256 fee      = (b.amount * FEE_BPS) / 10000;
        uint256 payout   = b.amount - fee;

        b.status = BountyStatus.Released;
        agents[b.provider].reputation += 10;

        require(usdc.transfer(b.provider, payout), "Payout failed");
        if (fee > 0) require(usdc.transfer(treasury, fee), "Fee transfer failed");

        emit BountyReleased(id, b.provider, payout);
        emit ReputationUpdated(b.provider, agents[b.provider].reputation);
    }

    /// @notice Cancel an open bounty and refund USDC to client
    function cancelBounty(bytes32 id) external {
        Bounty storage b = bounties[id];
        require(b.status == BountyStatus.Open, "Can only cancel open bounties");
        require(b.client == msg.sender, "Not the client");
        b.status = BountyStatus.Cancelled;
        require(usdc.transfer(msg.sender, b.amount), "Refund failed");
        emit BountyCancelled(id);
    }

    // ── Direct Escrow ────────────────────────────────────────────────────

    /// @notice Create a direct escrow between client and provider
    function createEscrow(bytes32 taskId, address provider, uint256 amount) external {
        require(escrows[taskId].client == address(0), "Escrow already exists");
        require(amount >= MIN_BOUNTY, "Minimum 1 USDC");
        require(usdc.transferFrom(msg.sender, address(this), amount), "USDC transfer failed");
        escrows[taskId] = Escrow({ client: msg.sender, provider: provider, amount: amount, released: false, refunded: false });
        emit EscrowCreated(taskId, msg.sender, provider, amount);
    }

    /// @notice Release escrow to provider (minus 0.5% fee)
    function releaseEscrow(bytes32 taskId) external {
        Escrow storage e = escrows[taskId];
        require(e.client == msg.sender, "Not client");
        require(!e.released && !e.refunded, "Already settled");
        e.released     = true;
        uint256 fee    = (e.amount * FEE_BPS) / 10000;
        uint256 payout = e.amount - fee;
        require(usdc.transfer(e.provider, payout), "Payout failed");
        if (fee > 0) require(usdc.transfer(treasury, fee), "Fee transfer failed");
        emit EscrowReleased(taskId, payout);
    }

    /// @notice Refund escrow back to client
    function refundEscrow(bytes32 taskId) external {
        Escrow storage e = escrows[taskId];
        require(e.client == msg.sender, "Not client");
        require(!e.released && !e.refunded, "Already settled");
        e.refunded = true;
        require(usdc.transfer(msg.sender, e.amount), "Refund failed");
        emit EscrowRefunded(taskId, e.amount);
    }

    // ── Admin ────────────────────────────────────────────────────────────
    function updateReputation(address agent, uint256 score) external onlyOwner {
        agents[agent].reputation = score;
        emit ReputationUpdated(agent, score);
    }

    function setTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
