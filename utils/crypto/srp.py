#pylint: disable=invalid-name
import hashlib
import hmac
from random import randint

from .dh import defaults
from .misc import bytes_to_long
""" Secure Remote Password implementation"""

N = defaults["p"]
g = 2
k = 3

def gen_verifier(password):
	salt = str(randint(0, 2**32 - 1)).encode()
	x_h = hashlib.sha256(salt + password).digest()
	x = bytes_to_long(x_h)
	verifier = pow(g, x, N)
	return salt, verifier

async def server_validate(get_verifier, send, recv):  #pylint: disable=too-many-locals
	email = await recv()
	salt, verifier = get_verifier(email)
	A = await recv()
	b = randint(0, N - 1)
	B = k * verifier + pow(g, b, N)
	await send(salt)
	await send(B)
	u_h = hashlib.sha256(str(A).encode() + str(B).encode()).digest()
	u = bytes_to_long(u_h)
	S = pow(A * pow(verifier, u, N), b, N)
	K = hashlib.sha256(str(S).encode()).digest()
	sent_digest = await recv()
	digest = hmac.digest(K, salt, hashlib.sha256)
	ok = hmac.compare_digest(digest, sent_digest)
	await send(ok)
	return ok

async def client_validate(email, password, send, recv):
	a = randint(0, N - 1)
	A = pow(g, a, N)
	await send(email)
	await send(A)
	salt = await recv()
	B = await recv()
	u_h = hashlib.sha256(str(A).encode() + str(B).encode()).digest()
	u = bytes_to_long(u_h)
	x_h = hashlib.sha256(salt + password).digest()
	x = bytes_to_long(x_h)
	S = pow(B - k * pow(g, x, N), a + u * x, N)
	K = hashlib.sha256(str(S).encode()).digest()
	await send(hmac.digest(K, salt, hashlib.sha256))
	return await recv()

async def client_zero_key(email, send, recv, A=0):
	if A % N != 0:
		raise ValueError("invalid A")
	await send(email)
	await send(A)
	salt = await recv()
	B = await recv()
	S = 0  # because pow(0,b,N) and pow(mult of N,b,N) both == 0
	K = hashlib.sha256(str(S).encode()).digest()
	await send(hmac.digest(K, salt, hashlib.sha256))
	return (K, await recv())
