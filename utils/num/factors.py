import math
import itertools
from collections import Counter

def sieve_of_eratosthenes(n):
	nums = [False, False] + [True for i in range(2, n + 1)]
	for i, prime in enumerate(nums[2:], start=2):
		if prime:
			for j in range(i * i, n + 1, i):
				nums[j] = False
	return (i for i, prime in enumerate(nums) if prime)

def sieve_of_eratosthenes2(n):
	nums = [True for i in range(2, n + 1)]
	p = 1
	try:
		while True:
			p = next(i for i, prime in enumerate(nums[p - 1:], start=p + 1) if prime)
			for i in range(2 * p, n + 1, p):
				nums[i - 2] = False
	except StopIteration:
		return (i for i, prime in enumerate(nums, start=2) if prime)

def prime_factors(n):
	while True:
		for i in range(2, int(math.sqrt(n)) + 1):
			if n % i == 0:
				yield i
				n /= i
				break
		else:
			yield int(n)
			return

def is_prime(n):
	return not any(n % i == 0 for i in range(2, int(math.sqrt(n)) + 1)) and n != 1

def proper_divisors(n):
	if n == 0 or n == 1:
		return
	yield 1
	for i in range(2, int(math.sqrt(n))):
		if n % i == 0:
			yield i
			yield n // i
	if math.floor(math.sqrt(n)) == math.sqrt(n):
		yield int(math.sqrt(n))

def is_abundant(n):
	return sum(proper_divisors(n)) > n

def factors(n):
	yield from proper_divisors(n)
	yield n

def num_factors(n):
	factors = Counter(prime_factors(n))
	return math.prod(c + 1 for c in factors.values())
