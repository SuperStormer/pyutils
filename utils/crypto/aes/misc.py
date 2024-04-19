import itertools
import os

from utils.itertools2 import grouper


def rand_aes_key():
	return os.urandom(16)


def detect_blocksize(oracle) -> int:
	initial_size = len(oracle(b""))
	for i in itertools.count(1):
		encrypted = oracle(b"A" * i)
		if len(encrypted) > initial_size:
			return len(encrypted) - initial_size
	raise ValueError("Could not detect block size")


def detect_ecb(oracle):
	plaintext = b"A" * 64
	blocks = list(map(bytes, grouper(oracle(plaintext), 16, fillvalue=0)))
	return len(blocks) != len(set(blocks))
