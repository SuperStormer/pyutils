import math
import random
from utils.num.ntheory import crt, egcd, modinv

#used for rsa problems where m^e < n meaning to decrypt c you can just do invpow(c,e)
#from https://stackoverflow.com/q/55436001/7941251
def invpow(x: int, n: int) -> int:
	"""Finds the integer component of the n'th root of x,
	an integer such that y ** n <= x < (y + 1) ** n.
	"""
	high = 1
	while high**n < x:
		high *= 2
	low = high // 2
	while low < high:
		mid = (low + high) // 2
		if low < mid and mid**n < x:
			low = mid
		elif high > mid and mid**n > x:
			high = mid
		else:
			return mid
	return mid + 1

# https://github.com/ashutosh1206/Crypton/tree/master/RSA-encryption/Factorisation-Fermat
def fermats_factorization(n):
	""" factor n by using difference of squares, only works if factors are close """
	a = math.isqrt(n) + 1
	b_2 = a**2 - n  # b squared
	while math.isqrt(b_2)**2 != b_2:
		a += 1
		b_2 = a**2 - n
	b = math.isqrt(b_2)
	return (a - b, a + b)

# see cryptopals 40
def hastad_broadcast_attack(cts, n_s, e):
	return invpow(crt(cts, n_s), e)

# see cryptopals 41
def decrypt_unpadded_oracle(c, e, n, oracle):
	s = random.randint(2, n - 1)
	c_prime = (pow(s, e, n) * c) % n
	p_prime = oracle(c_prime)
	return (p_prime * modinv(s, n)) % n

def common_mod_attack(c1, c2, e1, e2, n):
	""" pt is encrypted using 2 different e's but same n"""
	gcd, a, b = egcd(e1, e2)
	ct = (pow(c1, a, n) * pow(c2, b, n)) % n
	return invpow(ct, gcd)

def lsb_parity_oracle(c, e, n, oracle):
	# https://github.com/ashutosh1206/Crypton/tree/master/RSA-encryption/Attack-LSBit-Oracle
	upper = n
	lower = 0
	for _ in range(n.bit_length()):
		c = (c * pow(2, e, n)) % n
		if oracle(c):  #even
			upper = (upper + lower) // 2
		else:
			lower = (lower + upper) // 2
	return upper

def wieners_attack(e: int, n: int):
	""" returns d """
	#pylint: disable=import-outside-toplevel
	#lazy imports to avoid slowing down initial load
	from sympy.ntheory.continued_fraction import continued_fraction_convergents, continued_fraction_iterator
	from sympy.core.numbers import Rational
	c = 2
	convergents = continued_fraction_convergents(continued_fraction_iterator(Rational(e, n)))
	for convergent in convergents:
		d = convergent.denominator()
		p = pow(c, d, n)
		if pow(p, e, n) == c:
			return d
