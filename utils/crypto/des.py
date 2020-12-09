from Crypto.Cipher import DES
weak_keys = [
	b"\x01\x01\x01\x01\x01\x01\x01\x01", b"\xFE\xFE\xFE\xFE\xFE\xFE\xFE\xFE",
	b"\xE0\xE0\xE0\xE0\xF1\xF1\xF1\xF1", b"\x1F\x1F\x1F\x1F\x0E\x0E\x0E\x0E"
]

def all_weak_keys(ciphertext, iv):
	return [(DES.new(key, DES.MODE_OFB, iv).decrypt(ciphertext), key) for key in weak_keys]
