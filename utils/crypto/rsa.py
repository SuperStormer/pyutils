import math

from .misc import bytes_to_long, long_to_bytes
from Crypto.Util.number import getPrime

def modinv(a, m):
	return pow(a, -1, m)

def find_d(e, p, q):
	return modinv(e, totient(p, q))

def totient(p, q):
	return (p - 1) * (q - 1)

def decrypt(c, e, n, p, q=None):
	if q is None:
		q = n // p
	d = find_d(e, p, q)
	return pow(c, d, n)

def encrypt(m, e, n):
	return pow(m, e, n)

def decrypt_to_str(c, e, n, p, q=None):
	return long_to_bytes(decrypt(c, e, n, p, q))

def encrypt_str(m, e, n):
	return encrypt(bytes_to_long(m), e, n)

def multi_prime_totient(*args):
	return math.prod(c - 1 for c in args)

def multi_prime_find_d(e, *primes):
	return modinv(e, multi_prime_totient(*primes))

def multi_prime_decrypt(c, e, n, *primes):
	d = multi_prime_find_d(e, *primes)
	return pow(c, d, n)

def multi_prime_decrypt_to_str(c, e, n, *primes):
	return long_to_bytes(multi_prime_decrypt(c, e, n, *primes))

def gen_keypair(key_len, e=3):
	phi = 0
	while math.gcd(e, phi) != 1:
		p = getPrime(key_len // 2)
		q = getPrime(key_len // 2)
		phi = totient(p, q)
	n = p * q
	return (e, n, p, q)

#used for rsa problems where m^e < n meaning to decrypt c you can just do find_invpow(c,e)
#from https://stackoverflow.com/q/55436001/7941251
def invpow(x, n):
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
