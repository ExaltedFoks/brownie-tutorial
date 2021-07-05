#!/usr/bin/python3
from brownie import Contract
import pytest
from brownie_tokens import MintableForkToken


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def margarita(Token, accounts):
    return Token.deploy("Margarita", "MARG", 18, 1e21, {'from': accounts[0]})

@pytest.fixture(scope="module")
def alice(accounts):
    return accounts[0]

@pytest.fixture(scope="module")
def bob(accounts):
    return accounts[1]

def load_contract(addr):
    # pull contract if it exists, otherwise make an API call
    try:
        cont = Contract(addr)
    except ValueError:
        cont = Contract.from_explorer(addr)
    return cont

@pytest.fixture(scope="module")
def registry():
    provider = Contract("0x0000000022d53366457f9d5e68ec105046fc4383")

    return load_contract(provider.get_registry())

@pytest.fixture(scope="module")
def tripool(registry):
    return load_contract(registry.pool_list(0))

@pytest.fixture(scope="module")
def tripool_lp_token(registry, tripool):
    return load_contract(registry.get_lp_token(tripool))

@pytest.fixture(scope="module")
def tripool_funded(registry, alice, tripool):
    dai_addr = registry.get_coins(tripool)[0]
    dai = MintableForkToken(dai_addr)
    amount = 1e21
    dai.approve(tripool, amount, {'from': alice})
    dai._mint_for_testing(alice, amount)

    amounts = [amount, 0, 0]
    tripool.add_liquidity(amounts, 0, {'from': alice})
    return tripool
