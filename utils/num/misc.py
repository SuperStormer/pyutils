import math

#from https://stackoverflow.com/a/51716959/7941251
def lcm(a, b):
	return abs(a * b) // math.gcd(a, b)

#from https://stackoverflow.com/a/9758173/7941251
def egcd(a, b):
	if a == 0:
		return (b, 0, 1)
	else:
		g, y, x = egcd(b % a, a)
		return (g, x - (b // a) * y, y)

def reverse_num(n):
	m = 0
	while n != 0:  #iterate through digits right to left
		m *= 10
		m += n % 10
		n //= 10
	return m

def digit_sum(n):
	m = 0
	while n != 0:  #iterate through digits right to left
		m += n % 10
		n //= 10
	return m