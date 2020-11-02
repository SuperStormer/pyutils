from .xor import xor
from ..bits import lowest_bits
import random
import warnings

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
	
	def python_seed(self, n):
		"""python has some extra steps compared to classical MT
		see random_seed in https://github.com/python/cpython/blob/master/Modules/_randommodule.c"""
		#convert arbitary sized python int into array of 32-bit ints
		n = abs(n)
		key = []
		while n:
			key.append(lowest_bits(n, self.w))
			n >>= self.w
		self.init_by_array(key)
	
	def init_by_array(self, key):
		""" see init_by_array in https://github.com/python/cpython/blob/master/Modules/_randommodule.c """
		self.seed(19650218)
		i = 1
		j = 0
		for _ in range(max(self.n, len(key))):
			self.mt[i] = lowest_bits(
				(self.mt[i] ^ ((self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) * 1664525)) + key[j] + j,
				self.w
			)
			i += 1
			j += 1
			if i >= self.n:
				self.mt[0] = self.mt[self.n - 1]
				i = 1
			if j >= len(key):
				j = 0
		for _ in range(self.n - 1):
			self.mt[i] = lowest_bits(
				(self.mt[i] ^ ((self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) * 1566083941)) - i, self.w
			)
			i += 1
			if i >= self.n:
				self.mt[0] = self.mt[self.n - 1]
				i = 1
		self.mt[0] = 0x80000000
	
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
	
	def to_random(self):
		""" returns a random.Random with the same state"""
		rand = random.Random()
		# format is (version, internalstate, gauss_next)
		rand.setstate((3, tuple(self.mt + [self.index]), None))
		return rand

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

def copy_mersenne_twister(vals):
	vals = list(vals)
	state = list(map(untemper, vals))[:624]
	rand = MersenneTwister()
	if len(vals) > 624:
		# if there's more than 624 values, we can recover the index
		for i in range(1, 625):
			rand.mt = state[:]
			rand.index = i
			if rand.rand() == vals[624]:
				rand.mt = state
				rand.index = i
				#keep generating until it matches the current state
				for val in vals[624:]:
					assert rand.rand() == val
				break
		else:
			warnings.warn("Couldn't find internal index")
			rand.mt = state
			rand.index = rand.n
			return rand
	else:
		rand.mt = state
		rand.index = rand.n
	return rand

def copy_mersenne_twister2(rand):
	vals = [rand() for i in range(624)]
	return copy_mersenne_twister(vals)
