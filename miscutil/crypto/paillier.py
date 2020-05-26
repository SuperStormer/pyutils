from rsa import totient
""" https://en.wikipedia.org/wiki/Paillier_cryptosystem """

def L(x, n):
	return (x - 1) // n

# assuming g=n+1; returns (λ,μ) aka (lambda,mu)
def private_key(p, q):
	n = p * q
	g = n + 1
	lamb = totient(p, q)
	mu = pow(L(pow(g, lamb, n**2), n), -1, n)
	return (lamb, mu)

def decrypt(c, n, lamb, mu):
	return (L(pow(c, lamb, n**2), n) * mu) % n

def encrypt(m, n, g):
	raise NotImplementedError

def decrypt_to_str(c, n, lamb, mu):
	return bytes.fromhex(hex(decrypt(c, n, lamb, mu))[2:])

def encrypt_str(m, n, g):
	return encrypt(int("".join(hex(ord(c))[2:] for c in m), 16), n, g)
