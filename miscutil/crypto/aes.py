import os
import math
import itertools
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from xor import xor

def grouper(iterable, n, fillvalue=None):
	args = [iter(iterable)] * n
	return itertools.zip_longest(*args, fillvalue=fillvalue)

def round_to_multiple(x, y):
	return math.ceil(x / y) * y

def pad_pkcs7(s, block_size=16):
	length = round_to_multiple(len(s), block_size)
	pad_len = length - len(s)
	return s + bytes((pad_len, ) * pad_len)

def unpad_pkcs7(s, block_size=16):
	pad_length = s[-1]
	if pad_length > block_size:
		return s
	padding = s[-pad_length:]
	if all(c == padding[0] for c in padding):
		return s[:-pad_length]
	else:
		raise ValueError(f"Invalid PKCS#7 padding on {s!r}")

def aes_ecb(s, key, mode):
	cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
	if mode == "decrypt":
		func = cipher.decryptor()
	elif mode == "encrypt":
		s = pad_pkcs7(s, 16)
		func = cipher.encryptor()
	else:
		raise ValueError(f"Illegal mode {mode} is not 'decrypt' or 'encrypt' ")
	return func.update(s) + func.finalize()

def aes_cbc(s, key, iv, mode):
	if mode == "encrypt":
		s = pad_pkcs7(s, 16)
	blocks = map(bytes, grouper(s, 16))
	full_transformed = b""
	prev = iv
	for block in blocks:
		if mode == "encrypt":
			transformed = aes_ecb(xor(block, prev), key, mode)
			prev = transformed
			full_transformed += transformed
		else:
			transformed = aes_ecb(block, key, mode)
			full_transformed += xor(transformed, prev)
			prev = block
	return full_transformed

def aes_ctr(s, key, nonce):
	blocks = grouper(s, 16, None)
	num_blocks = math.ceil(len(s) / 16)
	full_transformed = b""
	for counter, block in enumerate(blocks):
		if counter == num_blocks - 1:  # strip None padding on last block
			block = itertools.takewhile(lambda x: x is not None, block)
		keystream = aes_ecb(struct.pack("<QQ", nonce, counter), key, "encrypt")
		transformed = xor(block, keystream)
		full_transformed += transformed
	return full_transformed

def rand_aes_key():
	return os.urandom(16)

def detect_blocksize(oracle):
	initial_size = len(oracle(b""))
	for i in itertools.count(1):
		encrypted = oracle(b"A" * i)
		if len(encrypted) > initial_size:
			return len(encrypted) - initial_size

def detect_aes_mode(oracle):
	plaintext = b"A" * 64
	blocks = list(map(bytes, grouper(oracle(plaintext), 16, 0)))
	if len(blocks) == len(set(blocks)):
		return "cbc"
	else:
		return "ecb"