from .xor import xor

class MersenneTwister:
	def __init__(self):
		self.w, self.n, self.m, self.r = 32, 624, 397, 31
		self.a = 0x9908b0df
		self.u, self.d = 11, 0xffffffff
		self.s, self.b = 7, 0x9d2c5680
		self.t, self.c = 15, 0xefc60000
		self.l = 18
		self.f = 1812433253
		self.lower_mask = (1 << self.r) - 1
		self.upper_mask = lowest_bits(-~self.lower_mask, self.w)
		self.mt = [0 for _ in range(self.n)]
		self.index = self.n + 1
	
	def seed(self, seed):
		self.index = self.n
		self.mt[0] = seed
		for i in range(1, self.n):
			self.mt[i] = lowest_bits(
				self.f * (self.mt[i - 1] ^ (self.mt[i - 1] >> (self.w - 2))) + i, self.w
			)
	
	def rand(self):
		if self.index >= self.n:
			if self.index > self.n:
				self.seed(5489)
			self.twist()
		y = self.mt[self.index]
		y ^= (y >> self.u) & self.d
		y ^= (y << self.s) & self.b
		y ^= (y << self.t) & self.c
		y ^= y >> self.l
		self.index += 1
		return lowest_bits(y, self.w)
	
	def twist(self):
		for i in range(self.n):
			x = (self.mt[i] & self.upper_mask) + (self.mt[(i + 1) % self.n] & self.lower_mask)
			xA = x >> 1
			if (x % 2) != 0:
				xA = xA ^ self.a
			self.mt[i] = self.mt[(i + self.m) % self.n] ^ xA
		self.index = 0

def lowest_bits(n, k):
	return n & ((1 << k) - 1)

#both funcs below from https://cypher.codes/writing/cryptopals-challenge-set-3
def unshift_right_xor(value, shift):
	result = 0
	for i in range(32 // shift + 1):
		result ^= value >> (shift * i)
	return result

def unshift_left_mask_xor(value, shift, mask):
	result = 0
	for i in range(0, 32 // shift + 1):
		part_mask = (0xffffffff >> (32 - shift)) << (shift * i)
		part = value & part_mask
		value ^= (part << shift) & mask
		result |= part
	return result

def untemper(y):
	u, d = 11, 0xffffffff
	s, b = 7, 0x9d2c5680
	t, c = 15, 0xefc60000
	l = 18
	y = unshift_right_xor(y, l)
	y = unshift_left_mask_xor(y, t, c)
	y = unshift_left_mask_xor(y, s, b)
	y = unshift_right_xor(y, u)
	return y

def copy_mersenne_twister(rand):
	vals = [rand.rand() for i in range(624)]
	state = list(map(untemper, vals))
	rand2 = MersenneTwister()
	rand2.mt = state
	rand2.index = rand2.n
	return rand2

def prng_stream_cipher(s, prng):
	return xor(s, iter(lambda: prng() % (2**8), None))

def mt_stream_cipher(s, seed):
	rand = MersenneTwister()
	rand.seed(seed)
	return prng_stream_cipher(s, rand.rand)
