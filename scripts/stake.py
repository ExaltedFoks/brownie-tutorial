from brownie import Contract, accounts, interface
from brownie_tokens import MintableForkToken

def main():
	dai_addr = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
	usdc_addr = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
	provider = Contract("0x0000000022d53366457f9d5e68ec105046fc4383")
	registry_addr = provider.get_registry()

	amount = 100_000 * 10 ** 18 # 18 decimal places, so 100,000 DAI
	dai = MintableForkToken(dai_addr)
	dai._mint_for_testing(accounts[0], amount)

	registry = Contract(registry_addr)
	pool_addr = registry.find_pool_for_coins(dai_addr, usdc_addr) # find pool that allows for transactions from DAI to USDC
	pool = Contract(pool_addr)

	dai.approve(pool_addr, amount, {'from': accounts[0]})
	pool.add_liquidity([amount, 0, 0], 0, {'from': accounts[0]}) # amount[DAI, USDC, USDT], min_amount, addresses

	gauges = registry.get_gauges(pool_addr)
	gauge_addr = gauges[0][0]
	gauge_contract = interface.LiquidityGauge(gauge_addr)

	lp_token = MintableForkToken(gauge_contract.lp_token())
	lp_token.approve(gauge_addr, amount, {'from': accounts[0]})
	gauge_contract.deposit(
		lp_token.balanceOf(accounts[0]),
		{'from': accounts[0]}
	)
