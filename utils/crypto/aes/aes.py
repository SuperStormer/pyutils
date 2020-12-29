"""actual encryption/decryption funcs"""
import itertools
import struct
from Crypto.Cipher import AES
from utils.itertools2 import grouper

from utils.crypto.padding import pad_pkcs7
from utils.crypto.xor import xor

def aes_ecb(s, key, mode, no_pad=False):
	cipher = AES.new(key, AES.MODE_ECB)
	if mode == "decrypt":
		func = cipher.decrypt
	elif mode == "encrypt":
		if not no_pad:
			s = pad_pkcs7(s, 16)
		func = cipher.encrypt
	else:
		raise ValueError(f"Illegal mode {mode!r} is not 'decrypt' or 'encrypt'")
	return func(s)

def aes_cbc(s, key, iv, mode):
	if mode not in ("encrypt", "decrypt"):
		raise ValueError(f"Illegal mode {mode!r} is not 'decrypt' or 'encrypt'")
	if mode == "encrypt":
		s = pad_pkcs7(s, 16)
	blocks = map(bytes, grouper(s, 16))
	full_transformed = b""
	prev = iv
	for block in blocks:
		if mode == "encrypt":
			transformed = aes_ecb(xor(block, prev), key, mode, no_pad=True)
			prev = transformed
			full_transformed += transformed
		else:
			transformed = aes_ecb(block, key, mode)
			full_transformed += xor(transformed, prev)
			prev = block
	return full_transformed

def aes_ctr_keystream(key, nonce):
	for counter in itertools.count():
		yield from aes_ecb(struct.pack("<QQ", nonce, counter), key, "encrypt", no_pad=True)

def aes_ctr(s, key, nonce):
	return xor(s, aes_ctr_keystream(key, nonce))
