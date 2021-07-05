from brownie import *

def shot(i):
	return Token.deploy(
			'Margarita',
			'MARG',
			18,
			1e21,
			{'from': accounts[i]}
			)

def main():
	for i in range(10):
		shot(i)