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

def hastad_broadcast_attack(cts, n_s, e):
	# see cryptopals 40
	return invpow(crt(cts, n_s), e)

def decrypt_unpadded_oracle(c, e, n, oracle):
	# see cryptopals 41
	s = random.randint(2, n - 1)
	c_prime = (pow(s, e, n) * c) % n
	p_prime = oracle(c_prime)
	return (p_prime * modinv(s, n)) % n

def common_mod_attack(c1, c2, e1, e2, n):
	gcd, a, b = egcd(e1, e2)
	ct = (pow(c1, a, n) * pow(c2, b, n)) % n
	return invpow(ct, gcd)

def lsb_parity_oracle(c, e, n, oracle):
	upper = n
	lower = 0
	for _ in range(n.bit_length()):
		c = (c * pow(2, e, n)) % n
		if oracle(c):  #even
			upper = (upper + lower) // 2
		else:
			lower = (lower + upper) // 2
	return upper

def wieners_attack(e: int, n: int) -> int:
	#pylint: disable=import-outside-toplevel
	#lazy imports to avoid slowing down initial load
	from sympy.ntheory import continued_fraction_convergents, continued_fraction_iterator
	from sympy import Rational
	c = 2
	convergents = continued_fraction_convergents(continued_fraction_iterator(Rational(e, n)))
	for convergent in convergents:
		d = convergent.denominator()
		p = pow(c, d, n)
		if pow(p, e, n) == c:
			return d
