from Crypto.Cipher import DES

weak_keys = [
	b"\x01\x01\x01\x01\x01\x01\x01\x01",
	b"\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe",
	b"\xe0\xe0\xe0\xe0\xf1\xf1\xf1\xf1",
	b"\x1f\x1f\x1f\x1f\x0e\x0e\x0e\x0e",
]


def all_weak_keys(ciphertext, iv):
	return [
		(DES.new(key, DES.MODE_OFB, iv).decrypt(ciphertext), key) for key in weak_keys
	]
