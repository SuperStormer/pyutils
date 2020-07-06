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