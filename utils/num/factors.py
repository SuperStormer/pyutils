import random
import math
from collections import Counter


def sieve_of_eratosthenes(n: int):
	nums = [False, False] + [True for i in range(2, n + 1)]
	for i, prime in enumerate(nums[2:], start=2):
		if prime:
			for j in range(i * i, n + 1, i):
				nums[j] = False
	return (i for i, prime in enumerate(nums) if prime)


def prime_factors(n: int):
	for i in range(2, math.isqrt(n) + 1):
		while n % i == 0:
			yield i
			n //= i
	if n != 1:
		yield n


def is_prime(n: int) -> bool:
	"""trial division with 6k +-1 optimization"""
	if n == 2 or n == 3:
		return True
	if n < 2 or n % 2 == 0 or n % 3 == 0:
		return False
	return not any(n % i == 0 or n % (i + 2) == 0 for i in range(5, math.isqrt(n) + 1, 6))


def is_probable_prime(n: int, k: int = 5) -> bool:
	"""Miller-Rabin test"""
	if n in (0, 1):
		return False
	if n % 2 == 0:
		return n == 2
	if n % 3 == 0:
		return n == 3
	d = n - 1
	r = 0
	while d % 2 == 0:
		d //= 2
		r += 1
	witnesses_dict = {
		2_047: (2,),
		1_373_653: (2, 3),
		9_080_191: (31, 73),
		25_326_001: (2, 3, 5),
		3_215_031_751: (2, 3, 5, 7),
		4_759_123_141: (2, 7, 61),
		1_122_004_669_633: (2, 13, 23, 1662803),
		2_152_302_898_747: (2, 3, 5, 7, 11),
		3_474_749_660_383: (2, 3, 5, 7, 11, 13),
		341_550_071_728_321: (2, 3, 5, 7, 11, 13, 17),
	}
	for key, val in witnesses_dict.items():
		if n < key:
			witnesses = val
			break
	else:
		witnesses = (random.randint(2, n - 2) for _ in range(k))
	for a in witnesses:
		x = pow(a, d, n)
		if x == 1 or x == n - 1:
			continue
		for _ in range(r - 1):
			x = pow(x, 2, n)
			if x == n - 1:
				break
		else:
			return False
	return True


def proper_divisors(n: int):
	if n == 0 or n == 1:
		return
	yield 1
	square_root = math.isqrt(n)
	for i in range(2, square_root):
		if n % i == 0:
			yield i
			yield n // i
	if pow(square_root, 2) == n:
		yield square_root


def factors(n: int):
	yield from proper_divisors(n)
	yield n


def is_abundant(n: int):
	return sum(proper_divisors(n)) > n


def num_factors(n: int) -> int:
	factors_counter = Counter(prime_factors(n))
	return math.prod(c + 1 for c in factors_counter.values())
