from utils.num.misc import round_to_multiple


def pad_pkcs7(s, block_size=16):
	length = round_to_multiple(len(s), block_size)
	pad_len = length - len(s)
	if pad_len == 0:
		pad_len = block_size
	return s + bytes((pad_len,) * pad_len)


def unpad_pkcs7(s):
	pad_length = s[-1]
	if all(c == pad_length for c in s[-pad_length:]):
		return s[:-pad_length]
	else:
		raise ValueError(f"Invalid PKCS#7 padding on {s!r}")
