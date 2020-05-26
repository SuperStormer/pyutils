"""
#both funcs below from https://stackoverflow.com/a/9758173/7941251
def egcd(a, b):
	if a == 0:
		return (b, 0, 1)
	else:
		g, y, x = egcd(b % a, a)
		return (g, x - (b // a) * y, y)

def modinv(a, m):
	g, x, y = egcd(a, m)
	if g != 1:
		raise ValueError('modular inverse does not exist')
	else:
		return x % m
"""

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
	return pow(c, d, n)  # equal to (c**d) % n

def encrypt(m, e, n):
	return pow(m, e, n)  # equal to (m**e) % n

def decrypt_to_str(c, e, n, p, q=None):
	return bytes.fromhex(hex(decrypt(c, e, n, p, q))[2:])

def encrypt_str(m, e, n):
	return encrypt(int("".join(hex(ord(c))[2:] for c in m), 16), e, n)

#used for rsa problems where m^e < n meaning to decrypt c you can just do find_invpow(c,e)
#from https://stackoverflow.com/q/55436001/7941251
def find_invpow(x, n):
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
