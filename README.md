# Brownie tutorial
## Pre-cursors
This series of tutorials assumes some familiarity with the following:
- Python
- working within the console
- smart contract development

Familiarity with smart contract development is not strictly needed, but you will have to pause a couple of times and google/read articles.

## TL;DR
Great tutorial on using Brownie to develop, interact, and test smart contracts. Assumes some familiarity with various technologies and moves fast, but goes over everything you need to start developing on Brownie. Covers everything about smart contract development *except* the contracts themselves.

Large focus on testing using `pytest` in the later chapters, drives home the importance of strong testing in smart contract development. Chapters 1-10 require basic Python knowledge, but 11+ require some intermediate knowledge.

The following are *my* notes as I went through the tutorial. This is **not** meant to be a summary nor replacement for the tutorials themselves. Instead, the notes will be used as reference for my future learning (and hopefully yours too!).

## Links
[The tutorial playlist](https://www.youtube.com/playlist?list=PLVOHzVzbg7bFUaOGwN0NOgkTItUAVyBBQ).

[Github repo](https://github.com/curvefi/brownie-tutorial).

[Brownie docs](https://eth-brownie.readthedocs.io/en/stable/).

[Curve docs](https://curve.readthedocs.io/).

### My installation issues

Currently stuck on the fourth [Curve brownie tutorial](https://www.youtube.com/watch?v=mN73VcjELp4&t=13s) because of an error with Brownie detailed by [this PR](https://github.com/eth-brownie/brownie/pull/1070). 

This only applies if your Mac short name (your user) has a dot in it (`first.last`), if you do not have a dot in your name this should not be an issue.

TLDR project path includes dotted filepath `/Users/first.last/Documents/brownie` and therefore cannot run. +1ed the PR hoping to get it fixed as well as sent a tweet @ the devs on Twitter. Hopefully a fix is implemented soon.
A workaround (if the devs don't respond in time) is to fork the PR repo, rebase the PR branch w/ Curve master, and then install as my local brownie. This solved the issue.

If you're doing this workaround, make sure to use virtualenv first `source venv/bin/activate` inside of the forked brownie repo in order to use dev version of Brownie locally. See [this](https://github.com/eth-brownie/brownie/blob/master/CONTRIBUTING.md) page for more details.

### 5. Transactions
`brownie test tests/test_mint.py --interactive`. The interactive test flag sends you into a brownie console if a test fails at the moment of failure. This is unbelievably based.

`conftest.py` is in charge of configuration for *all* tests. This is where you would put a ERC20 token creation that can be used in the rest of your tests. Notice the scope is defined as `module`. Ex:
```python
@pytest.fixture(scope="module")
def margarita(Token, accounts):
    return Token.deploy("Margarita", "MARG", 18, 1e21, {'from': accounts[0]})
```

`history` is an array w/ full history of txs. `history[1].info()` for info about second transaction.

`transfer_tx = chain.get_transaction(tx_id)` assigns transaction hash to a variable so you don't have to call from the full hash each time. `transfer_tx` is a transaction object, so you can call `transfer_tx.info()` or similar fns.

### 6. Tokens
https://infura.io/ allows access to mainnet-fork. Export the key as a variable such as this `export WEB3_INFURA_PROJECT_ID=_your_infura_key_` in order to access mainnet-fork.

Package [Brownie Token Tester](https://pypi.org/project/brownie-token-tester/) provides helper objects for generating ERC20s while testing a Brownie project. For example, `MintableForkToken` allows us to easily mint 100000 DAI for testing.

Brownie `Contract` object allows for interaction w/ a deployed contract that is not a part of current project:
```python
from brownie import Contract
contract_object = Contract(_addr_)
```

Run mainnet fork: `brownie console --network mainnet-fork`

### 7. Interfaces
Brownie From Explorer: brownie contract function to fetch a contract's ABI from Etherscan. Use: `Contract.from_explorer(<contract_addr>)`

Vyper has a built in function to create external interfaces from contracts.
`vyper -f external_interface <contract>`. Similar functionality for abi through `vyper -f abi <contract.vy> > <contract.json>`. 

Store in the brownie interfaces/ directory as any one of the following:
```
Solidity (.sol)
Vyper (.vy)
ABI (.json)
```

Brownie cannot understand the gauge contract in isolation. Instead, have to create an interface first (through the above steps), and then call using
```python
from brownie import interface
contract = interface.<file_handle>(<contract_addr>)
# ex:
gauge_contract = interface.LiquidityGauge(gauge_addr)
```
This is why later scripts employ the following to pull an abi using from_explorer if it doesn't exist, or load from local database:
```python
def load_contract(addr):
    # pull contract if it exists, otherwise make an API call
    try:
        cont = Contract(addr)
    except ValueError:
        cont = Contract.from_explorer(addr)
    return cont
```


### 8. Fixture 1
Brownie uses pytest.

A *fixture* is a function that is applied to one or more test functions, and is called prior to the execution of each test. Fixtures are used to setup the initial conditions required for a test.

Declared using the `@pytest.fixture(scope="module")` operator. Pytest looks for fixtures in `/tests/conftest.py` as mentioned in the [[#5 Transactions | transactions section]]. Fixtures can be passed as arguments in your other tests. Basic example is deploying a token, then using that deployed token as an argument for other tests to build on.

Fixture scopes:
- function: \<default> fixture destroyed at end of test
- class: fixture destroyed at last test in class
- module: fixture destroyed at last test in module
- fixture: fixture destroyed at end of session

### 9. Fixtures II
Brownie contract persistence: after being created once, brownie stores a copy of contracts in a local database that persists between sessions.

With fixtures, you can use other fixtures as arguments. For example
```python
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
```
Testing these fixtures is much more simple, simply pull the fixtures in as arguments for each test.

Ensure you specify the network for tests using the `brownie test tests/test_curve.py --network mainnet-fork`.

### 10. Parametrization
Previous tests were stateful, with a pre-determined outcome. Parametrization allows you to run tests repeatedly over a wide range of dynamic inputs.

Parametrized tests are slow, so they are often contained in a different directory and run seperately.
`brownie test tests/unitary` <- non-parametrized tests
`brownie test tests/integrative` <- parametrized tests

Don't have to import fixtures to other tests, but do have to import other testing functions as you normally would in Python.

The following will parametrize a test, running the test 10 times with an i parameter of int values 0 to 9.
```python
@pytest.mark.parametrize('i', range(10))
def test_3pool_redeposit(alice, registry, tripool_funded, tripool_lp_token, i):
```
Integrative tests currently taking forever because I haven't provided an Etherscan API key, therefore likely getting rate-limited. Integrative tests can often times get into the hundreds, and therefore an API key would be useful. Export as environment variable `export ETHERSCAN_TOKEN=_your_etherscan_token_`.

### 11. Chain I
Chapter on the Brownie [chain object](https://eth-brownie.readthedocs.io/en/stable/core-chain.html).

`chain.snapshot()` allows you to capture a specific time in the chain. You can run a bunch of transactions, and then rewind (`chain.revert()`) back to state of the chain at the time of the snapshot. The snapshot is never consumed, so you can rewind as often as needed.

`chain.undo()` and `chain.redo()` is especially useful during interactive test debugging. This is used to move backwards and forwards through recent transactions.

This chapter goes over a way to determine all the possible meta 3pools that exist, and the LP returns over each one.

### 12. Chain II
The script we're developing is abstract such that it can be used on any address (w/ minimal configuration). Can try to extend this functionality later to other LPs such as Sushiswap.

The dev notes that the incessant looping is the brute force method - much more elegant solutions can be employed by making use of the many registry functions. As a result, this code will take a while (and will make a lot of unnecessary infura calls).