import math
import secrets

from .misc import long_to_bytes, bytes_to_long
from ..num.misc import lcm
""" https://en.wikipedia.org/wiki/Paillier_cryptosystem """

def L(x, n):
	return (x - 1) // n

def private_key(p, q, g):
	n = p * q
	lamb = lcm(p - 1, q - 1)
	mu = pow(L(pow(g, lamb, n**2), n), -1, n)
	return (lamb, mu)

def decrypt(c, n, lamb, mu):
	return (L(pow(c, lamb, n**2), n) * mu) % n

def encrypt(m, n, g):
	r = -1
	while math.gcd(r, n) != 1 and r != 0:
		r = secrets.randbelow(n)
	return (pow(g, m, n**2) * pow(r, n, n**2)) % n**2

def decrypt_to_str(c, n, lamb, mu):
	return long_to_bytes(decrypt(c, n, lamb, mu))

def encrypt_str(m, n, g):
	return encrypt(bytes_to_long(m), n, g)
