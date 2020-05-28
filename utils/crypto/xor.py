import string
import itertools

def xor(s, t):
	return bytes(a ^ b for a, b in zip(s, t))

letter_frequencies = {
	"a": 8.497,
	"b": 1.492,
	"c": 2.202,
	"d": 4.253,
	"e": 11.162,
	"f": 2.228,
	"g": 2.015,
	"h": 6.094,
	"i": 7.546,
	"j": 0.153,
	"k": 1.292,
	"l": 4.025,
	"m": 2.406,
	"n": 6.749,
	"o": 7.507,
	"p": 1.929,
	"q": 0.095,
	"r": 7.587,
	"s": 6.327,
	"t": 9.356,
	"u": 2.758,
	"v": 0.978,
	"w": 2.560,
	"x": 0.150,
	"y": 1.994,
	"z": 0.077
}

def english_like(s: str) -> float:
	"""higher is better"""
	if any(c not in string.printable for c in s):
		return -1
	return sum(letter_frequencies.get(c, 0) for c in s)

def decrypt_one_byte_xor(s):
	"""returns (plaintext,key)"""
	return max(
		((xor(s, itertools.repeat(c)).decode("utf-8", errors="ignore"), c) for c in range(256)),
		key=lambda x: english_like(x[0])
	)

def repeating_key_xor(s, k):
	return xor(s, itertools.cycle(k))

def hamming(s: bytes, t: bytes):
	dist = 0
	for i, j in zip(s, t):
		if i is None or j is None:
			dist += 8
		else:
			dist += bin(i ^ j).count("1")
	return dist

# from https://docs.python.org/3/library/itertools.html
def grouper(iterable, n, fillvalue=None):
	args = [iter(iterable)] * n
	return itertools.zip_longest(*args, fillvalue=fillvalue)

def decrypt_repeating_xor(s, min_len=2, max_len=40, keysizes_to_try=3):
	"""returns (plaintext,key)"""
	#average hamming distance of first 4 key_size len chunks
	key_sizes = sorted(
		range(min_len, max_len + 1),
		key=lambda i: sum(hamming(s[i * (j - 1):i * j], s[i * j:i * (j + 1)]) for j in range(4)) /
		(4 * i)
	)
	keys = []
	
	for key_size in key_sizes[:keysizes_to_try]:
		blocks = list(grouper(s, key_size, fillvalue=0))
		transposed_blocks = [bytes(block[i] for block in blocks) for i in range(key_size)]
		key = bytes(decrypt_one_byte_xor(block)[1] for block in transposed_blocks)
		keys.append((repeating_key_xor(s, key), key))
	return max(keys, key=lambda x: english_like(x[0].decode("utf-8")))
