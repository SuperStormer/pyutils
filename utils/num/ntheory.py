import math
"""Number Theory functions"""

#from https://stackoverflow.com/a/51716959/7941251
def lcm(a, b):
	return abs(a * b) // math.gcd(a, b)

#from https://stackoverflow.com/a/9758173/7941251
def egcd(a, b):
	if a == 0:
		return (b, 0, 1)
	else:
		g, y, x = egcd(b % a, a)
		return (g, x - (b // a) * y, y)

def modinv(a, m):
	return pow(a, -1, m)

# var names from https://crypto.stanford.edu/pbc/notes/numbertheory/crt.html
def crt(a_s, moduli):
	""" Chinese Remainder Theorem"""
	x = 0
	M = math.prod(moduli)
	for a, m in zip(a_s, moduli):
		b = M // m
		b_prime = modinv(b, m)
		x += a * b * b_prime
	return x % M
