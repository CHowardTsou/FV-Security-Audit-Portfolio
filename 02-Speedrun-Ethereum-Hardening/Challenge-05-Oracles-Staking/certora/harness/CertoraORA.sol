// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

contract CertoraORA {
    string public constant name = "Oracle Token";
    string public constant symbol = "ORA";
    uint8 public constant decimals = 18;

    mapping(address => uint256) private balances;
    mapping(address => mapping(address => uint256)) private allowances;
    uint256 private supply;

    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    function setBalance(address account, uint256 amount) external {
        balances[account] = amount;
    }

    function setAllowance(address owner, address spender, uint256 amount) external {
        allowances[owner][spender] = amount;
    }

    function balanceOf(address account) external view returns (uint256) {
        return balances[account];
    }

    function totalSupply() external view returns (uint256) {
        return supply;
    }

    function allowance(address owner, address spender) external view returns (uint256) {
        return allowances[owner][spender];
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        if (balances[msg.sender] < amount) return false;
        balances[msg.sender] -= amount;
        balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        if (balances[from] < amount) return false;
        uint256 allowed = allowances[from][msg.sender];
        if (allowed < amount) return false;
        allowances[from][msg.sender] = allowed - amount;
        balances[from] -= amount;
        balances[to] += amount;
        emit Transfer(from, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) external {
        balances[to] += amount;
        emit Transfer(address(0), to, amount);
    }
}
