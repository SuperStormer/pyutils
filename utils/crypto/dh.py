"""Diffie-Hellman implementation"""

defaults = {
	"p": int(
		"""ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024
	e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd
	3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec
	6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f
	24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361
	c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552
	bb9ed529077096966d670c354e4abc9804f1746c08ca237327fff
	fffffffffffff""".replace("\n", "").replace("\t", ""),
		16,
	),
	"g": 2,
}


def public_key(g, a, p):
	"""g is the base, a is the private key, p is the modulus"""
	return pow(g, a, p)


def shared_secret(a, B, p):  # noqa: N803
	"""a is your private key, B is partner's public key, p is the modulus"""
	return pow(B, a, p)
