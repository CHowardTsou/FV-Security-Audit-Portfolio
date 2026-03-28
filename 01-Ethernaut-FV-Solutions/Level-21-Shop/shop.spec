methods {
    function price() external returns (uint256) envfree;
    function isSold() external returns (bool) envfree;
    function buy() external;
    function _.price() external => togglePrice() expect(uint256);
}

ghost mathint g_count {
    init_state axiom g_count == 0;
}

function togglePrice() returns (uint256) {
    if (g_count == 0) {
        g_count = g_count + 1;
        return 100;
    } else {
        return 1;
    }
}

rule price_is_manipulated(env e) {
    bool soldBefore = isSold();
    require !soldBefore;

    // We expect the price to be 100 initially
    require price() == 100;

    buy(e);

    // THE SECURITY PROOF: 
    // We prove that a buyer can set the price to something lower than 100.
    // Certora will find a violation here because your ghost returns 1.
    assert isSold() => price() >= 100, "Security Breach: Item sold for less than the asking price!";
}
