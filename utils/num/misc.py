import math
import string


def reverse_num(n: int) -> int:
	m = 0
	while n != 0:  # iterate through digits right to left
		m *= 10
		m += n % 10
		n //= 10
	return m


def digit_sum(n: int) -> int:
	m = 0
	while n != 0:  # iterate through digits right to left
		m += n % 10
		n //= 10
	return m


def round_to_multiple(x: int, y: int) -> int:
	return math.ceil(x / y) * y


_base_alphabet = string.digits + string.ascii_lowercase


def to_base(n: int, base: int, _alphabet: str = _base_alphabet) -> str:
	if base in (-1, 0, 1):
		raise ValueError(f"base cannot be {base}")
	if n == 0:
		return _alphabet[0]
	if n < 0:
		sign = "-"
		n *= -1
	else:
		sign = ""
	out = []
	while n:  # iterate through digits right to left
		out.append(_alphabet[n % base])
		n //= base
	return sign + "".join(reversed(out))
