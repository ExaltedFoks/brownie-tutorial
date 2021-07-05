from brownie import *
from brownie_tokens import MintableForkToken


def load_contract(addr):
    # pull contract if it exists, otherwise make an API call
    if addr = ZERO_ADDRESS:
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


def run_operations(_pool, _pool_index, contract):
	f


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
