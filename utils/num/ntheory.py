"""Number Theory functions"""

import math
import sys

if sys.version_info >= (3, 9):
	lcm = math.lcm
else:
	# from https://stackoverflow.com/a/51716959/7941251
	def lcm(a: int, b: int) -> int:
		return abs(a * b) // math.gcd(a, b)


# from https://stackoverflow.com/a/9758173/7941251
def egcd(a: int, b: int):
	if a == 0:
		return (b, 0, 1)
	else:
		g, y, x = egcd(b % a, a)
		return (g, x - (b // a) * y, y)


def modinv(a: int, m: int) -> int:
	return pow(a, -1, m)


# var names from https://crypto.stanford.edu/pbc/notes/numbertheory/crt.html
def crt(a_s: list[int], moduli: list[int]) -> int:
	"""Chinese Remainder Theorem"""
	x = 0
	M = math.prod(moduli)  # noqa: N806
	for a, m in zip(a_s, moduli):
		b = M // m
		b_prime = modinv(b, m)
		x += a * b * b_prime
	return x % M
