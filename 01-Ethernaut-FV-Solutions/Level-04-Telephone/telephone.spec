methods {
    function owner() external returns (address) envfree;
}

rule integrityOfOwnership(env e, method f, calldataarg args) {
    // pre-condition
    address oldOwner = owner();

    // calls
    f(e, args);

    // post-condition
    address newOwner = owner();

    // assert
    assert e.msg.sender != oldOwner => oldOwner == newOwner;
}
