# from https://www.falatic.com/index.php/108/python-and-bitwise-rotation
# rotate left
def rol(val: int, r_bits: int, max_bits: int):
	return (val << r_bits % max_bits) & (2**max_bits - 1) | (
		(val & (2**max_bits - 1)) >> (max_bits - (r_bits % max_bits))
	)


# rotate right
def ror(val: int, r_bits: int, max_bits: int):
	return ((val & (2**max_bits - 1)) >> r_bits % max_bits) | (
		val << (max_bits - (r_bits % max_bits)) & (2**max_bits - 1)
	)


def lowest_bits(n: int, k: int):
	return n & ((1 << k) - 1)
