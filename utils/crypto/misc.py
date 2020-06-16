import string

def long_to_bytes(x):
	return x.to_bytes((x.bit_length() + 7) // 8, byteorder="big")

def bytes_to_long(x):
	return int.from_bytes(x, byteorder="big")

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

def hamming(s: bytes, t: bytes):
	dist = 0
	for i, j in zip(s, t):
		if i is None or j is None:
			dist += 8
		else:
			dist += bin(i ^ j).count("1")
	return dist