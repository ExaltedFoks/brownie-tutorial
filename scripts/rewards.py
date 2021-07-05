from brownie import *
from brownie_tokens import MintableForkToken


def load_contract(addr):
    # pull contract if it exists, otherwise make an API call
    if addr == ZERO_ADDRESS:
    	return None
    try:
        cont = Contract(addr)
    except ValueError:
        cont = Contract.from_explorer(addr)
    return cont


# load globals
whale = accounts[0]
provider = Contract("0x0000000022d53366457f9d5e68ec105046fc4383")

registry = load_contract(provider.get_registry())
minter = load_contract('0xd061D61a4d941c39E5453435B6345Dc261C2fcE0')
crv = load_contract(minter.token())


def add_tripool_liquidity():
	dai_addr = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
	usdc_addr = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

	amount = 100_000 * 10 ** 18 # 18 decimal places, so 100,000 DAI
	dai = MintableForkToken(dai_addr)
	dai._mint_for_testing(whale, amount)

	pool_addr = registry.find_pool_for_coins(dai_addr, usdc_addr) # find pool that allows for transactions from DAI to USDC
	pool = Contract(pool_addr)

	dai.approve(pool_addr, amount, {'from': whale})
	pool.add_liquidity([amount, 0, 0], 0, {'from': whale}) # amount[DAI, USDC, USDT], min_amount, addresses

	return pool


def run_operations(_pool, _pool_index, tripool_lp):
	# take a chain snapshot
	chain.snapshot()

	# ape into a pool
	ape(_pool, _pool_index, tripool_lp)

	# skip forward 1 day
	chain.mine(timedelta=60*60*24) # skip forward one day and mine a block

	# check CRV balance
	_val = calc_cur_value()
	_name = registry.get_pool_name(_pool)

	# revert
	chain.revert()
	return _name, _val


def ape(pool, pool_index, tripool_lp):
	# approve deposit from tripool into metapool
	tripool_bal = tripool_lp.balanceOf(whale)
	tripool_lp.approve(pool, tripool_bal, {'from': whale})

	# add liquidity
	amounts = [0] * registry.get_n_coins(pool)[0]
	amounts[pool_index] = tripool_bal
	pool.add_liquidity(amounts, 0, {'from': whale})

	# check if pool has gauge
	gauge_addr = registry.get_gauges(pool)[0][0]
	if gauge_addr == ZERO_ADDRESS:
		return

	# create approval for the rewards pool
	pool_lp = load_contract(registry.get_lp_token(pool))
	pool_bal = pool_lp.balanceOf(whale)
	if pool_lp.allowance(whale, gauge_addr) < pool_bal:
		pool_lp.approve(gauge_addr, pool_bal, {'from': whale})

	# make a deposit
	gauge = load_contract(gauge_addr)
	gauge.deposit(pool_bal, {'from': whale})


def calc_cur_value():
	# get initial value
	init_val = _calc_balance() # accounts[0] has nothing, but for future use w/ real addresses

	# set CRV claim array
	crv_pools = [ZERO_ADDRESS] * 8
	j = 0
	for i in range(registry.pool_count()):
		# check if gauge exists
		_addr = registry.get_gauges(registry.pool_list(i))[0][0]
		if _addr == ZERO_ADDRESS:
			continue

		# add gauge to claim if balance
		_gauge = load_contract(_addr)
		if _gauge.balanceOf(whale) > 0:
			crv_pools[j] = _addr
			j += 1

	# mint many
	minter.mint_many(crv_pools, {'from': whale})

	# calculate our balance
	final_val = _calc_balance()

	# undo mint many
	chain.undo() # rewinds our single blockchain transaction of "mint_many"
	return final_val - init_val


def _calc_balance():
	return crv.balanceOf(whale) / 10 ** crv.decimals()


def main():
	# check initial value
	strategy = {}
	init_value = calc_cur_value()
	strategy['init'] = init_value
	print(f"Initially {init_value}")

	# assign DAI to 3pool
	tripool = add_tripool_liquidity()
	tripool_lp = registry.get_lp_token(tripool)


	# loop through all pools that accept 3pool
	for i in range(registry.pool_count()):
		_pool_addr = registry.pool_list(i)
		_pool = load_contract(_pool_addr)
		# why just the first value in get_n_coins? Maybe 3pool is always the first if it's in a meta pool
		for j in range(registry.get_n_coins(_pool)[0]):
			if _pool.coins(j) == tripool_lp:
				_name, _val = run_operations(_pool, j, load_contract(tripool_lp))
				strategy[_name] = _val
				print(f"{_name}: {_val}")

	# print strategy summary
	for key, value in sorted(strategy.items(), key=lambda item: -item[1]):
		print(key, value)
