import itertools

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

def collatz(n):
	while n != 1:
		yield n
		if n % 2 == 0:
			n = n // 2
		else:
			n = 3 * n + 1
	yield 1
