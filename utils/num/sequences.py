import itertools
from functools import lru_cache


def triangular_nums():
	n = 0
	for i in itertools.count(1):
		n += i
		yield n


def fib():
	yield 1
	a = 1
	b = 1
	while True:
		a, b = b, a + b
		yield a


@lru_cache(maxsize=512)
def nth_fib(n: int) -> int:
	"""uses fast doubling(see https://www.nayuki.io/page/fast-fibonacci-algorithms)"""
	if n == 0:
		return 0
	elif n == 1 or n == 2:
		return 1
	x = nth_fib(n // 2)
	y = nth_fib(n // 2 + 1)
	if n % 2 == 0:
		return x * (2 * y - x)
	else:
		return x**2 + y**2


@lru_cache(maxsize=512)
def nth_fib_rec(n: int) -> int:
	"""uses standard recursive algorithm"""
	if n == 0:
		return 0
	if n == 1:
		return 1
	return nth_fib(n - 1) + nth_fib(n - 2)


phi = (1 + 5**0.5) / 2


def nth_fib_binet(n: int) -> int:
	"""uses Binet's formula"""
	return round((phi**n - (1 - phi) ** n) / (5**0.5))


def collatz(n):
	while n != 1:
		yield n
		if n % 2 == 0:
			n = n // 2
		else:
			n = 3 * n + 1
	yield 1
