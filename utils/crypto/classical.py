import string
import itertools
from .misc import english_like

def caesar_all(s, alphabet_only=True):
	if alphabet_only:
		return ((caesar(s, i, alphabet_only), i) for i in range(26))
	else:  #full ascii
		return ((caesar(s, i, alphabet_only), i) for i in range(128))

def caesar(s, shift, alphabet_only=True):
	if alphabet_only:
		return "".join(
			chr((ord(c) + shift - 65) % 26 +
			65) if c.isupper() else chr((ord(c) + shift - 97) % 26 + 97) if c.islower() else c
			for c in s
		)
	else:  #full ascii
		return "".join(chr((ord(c) + shift) % 128) for c in s if (ord(c) + shift) % 128 > 31)

def decrypt_caesar(s, alphabet_only=True):
	"""returns (plaintext,key) """
	return max(caesar_all(s, alphabet_only), key=lambda x: english_like(x[0]))

def vigenere(s, key, mode):
	key = key.lower()
	if mode == "encrypt":
		return "".join(
			chr((ord(c) + string.ascii_lowercase.index(d) - 65) % 26 +
			65) if c.isupper() else chr((ord(c) + string.ascii_lowercase.index(d) - 97) % 26 +
			97) if c.islower() else c for c, d in zip(s, itertools.cycle(key))
		)
	else:
		return "".join(
			chr((ord(c) - string.ascii_lowercase.index(d) - 65) % 26 +
			65) if c.isupper() else chr((ord(c) - string.ascii_lowercase.index(d) - 97) % 26 +
			97) if c.islower() else c for c, d in zip(s, itertools.cycle(key))
		)
