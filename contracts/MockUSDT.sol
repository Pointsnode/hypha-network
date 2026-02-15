// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/**
 * @title MockUSDT
 * @notice Mock USDT token for testing purposes
 * @dev Uses 6 decimals like real USDT
 */
contract MockUSDT is ERC20 {
    constructor() ERC20("Mock USDT", "USDT") {
        // Mint initial supply to deployer for testing
        _mint(msg.sender, 1000000 * 10**6); // 1 million USDT
    }

    /**
     * @notice USDT uses 6 decimals (not 18 like standard ERC20)
     */
    function decimals() public pure override returns (uint8) {
        return 6;
    }

    /**
     * @notice Mint tokens to any address (for testing only)
     * @param to Address to mint tokens to
     * @param amount Amount to mint (in USDT units with 6 decimals)
     */
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }

    /**
     * @notice Burn tokens from caller (for testing)
     * @param amount Amount to burn
     */
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}
