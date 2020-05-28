from .misc import long_to_bytes, bytes_to_long

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
