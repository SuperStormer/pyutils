import itertools
from typing import NamedTuple

from utils.itertools2 import grouper

from .misc import english_like, hamming

class XorResult(NamedTuple):
	text: bytes
	key: bytes

def xor(s, t) -> bytes:
	return bytes(a ^ b for a, b in zip(s, t))

def one_byte_xor_all(s: bytes):
	return (XorResult(xor(s, itertools.repeat(c)), bytes([c])) for c in range(256))

def decrypt_one_byte_xor(s: bytes) -> XorResult:
	return max(
		one_byte_xor_all(s), key=lambda x: english_like(x.text.decode("utf-8", errors="ignore"))
	)

def repeating_key_xor(s, k):
	return xor(s, itertools.cycle(k))

def repeating_key_xor_all(s, min_len=2, max_len=40, keysizes_to_try=3) -> list[XorResult]:
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
		key = b"".join(decrypt_one_byte_xor(block).key for block in transposed_blocks)
		keys.append(XorResult(repeating_key_xor(s, key), key))
	return keys

def decrypt_repeating_key_xor(s, min_len=2, max_len=40, keysizes_to_try=3):
	return max(
		repeating_key_xor_all(s, min_len, max_len, keysizes_to_try),
		key=lambda x: english_like(x[0].decode("utf-8", errors="ignore"))
	)
