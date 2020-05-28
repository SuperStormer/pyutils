"""Diffie-Hellman implementation"""

def public_key(g, a, p):
	"""g is the base, a is the private key, p is the modulus"""
	return pow(g, a, p)

def shared_secret(a, B, p):
	"""a is your private key, B is partner's public key, p is the modulus"""
	return pow(B, a, p)
