MULTIPLIER = 0x5DEECE66D
ADDEND = 0xB

class JavaRandom():
	def __init__(self, seed):
		self.seed = seed
	
	def next(self, bits=32):
		self.seed = (self.seed * MULTIPLIER + ADDEND) & ((1 << 48) - 1)
		res = self.seed >> (48 - bits)
		#deal with java's signed ints
		if res & (1 << 31):
			return -(1 << 32) + res
		else:
			return res
	
	rand = next
	
	def next_int(self, bound):
		if bound <= 0:
			raise ValueError("bound must be positive")
		
		if (bound & -bound) == bound:  # i.e., bound is a power of 2
			return (bound * self.next(31)) >> 31
		bits = 0
		val = 0
		while bits - val + (bound - 1) < 0:
			bits = self.next(31)
			val = bits % bound
		return val
	
	def next_long(self):
		return (self.next(32) << 32) + self.next(32)
	
	def next_float(self):
		return self.next(24) / ((1 << 24))
	
	def next_double(self):
		return ((self.next(26) << 27) + self.next(27)) / (1 << 53)

# https://github.com/fta2012/ReplicatedRandom/blob/master/ReplicatedRandom.java#L32
def find_seed(x, y):
	""" find seed based on two next(32) calls """
	#deal with Java signed ints
	if x < 0:
		x += 1 << 32
	if y < 0:
		y += 1 << 32
	
	mask = (1 << 48) - 1
	upper_m_of_48_mask = ((1 << 32) - 1) << (48 - 32)
	old_seed_upper_n = (x << (48 - 32)) & mask
	new_seed_upper_m = (y << (48 - 32)) & mask
	
	for old_seed in range(old_seed_upper_n, (old_seed_upper_n | ((1 << (48 - 32)) - 1)) + 1):
		new_seed = (old_seed * MULTIPLIER + ADDEND) & mask
		if (new_seed & upper_m_of_48_mask) == new_seed_upper_m:
			return new_seed

# https://stackoverflow.com/q/32324404
def find_seed_long(l):
	""" find seed based on one nextLong() call """
	y = l & 0xFFFFFFFF
	x = (l - y) >> 32
	return find_seed(x, y)

# https://stackoverflow.com/q/32324404
def prev_seed(seed):
	""" find the previous seed given the current seed """
	inv_multiplier = 0xDFE05BCB1365
	mask = 0xFFFFFFFFFFFF
	return ((seed - ADDEND) * inv_multiplier) & mask

def copy_random(x, y):
	""" from 2 randInt calls """
	seed = find_seed(x, y)
	rand = JavaRandom(seed)
	return rand
