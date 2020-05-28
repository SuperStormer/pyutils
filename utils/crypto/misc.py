def long_to_bytes(x):
	return x.to_bytes((x.bit_length() + 7) // 8, byteorder="big")

def bytes_to_long(x):
	return int.from_bytes(x, byteorder="big")
