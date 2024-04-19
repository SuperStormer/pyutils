#!/usr/bin/env python3
# adapted from https://github.com/TACIXAT/XorShift128Plus
import random
import struct

from z3 import BitVecs, Bool, Implies, LShR, Or, Solver, sat

MASK = 0xFFFFFFFFFFFFFFFF


# xor_shift_128_plus algorithm
def xs128p(state0, state1, browser):
	s1 = state0 & MASK
	s0 = state1 & MASK
	s1 ^= (s1 << 23) & MASK
	s1 ^= (s1 >> 17) & MASK
	s1 ^= s0 & MASK
	s1 ^= (s0 >> 26) & MASK
	state0 = state1 & MASK
	state1 = s1 & MASK
	if browser == "chrome":
		generated = state0 & MASK
	else:
		generated = (state0 + state1) & MASK

	return state0, state1, generated


# Symbolic execution of xs128p
def sym_xs128p(slvr, sym_state0, sym_state1, generated, browser):
	s1 = sym_state0
	s0 = sym_state1
	s1 ^= s1 << 23
	s1 ^= LShR(s1, 17)
	s1 ^= s0
	s1 ^= LShR(s0, 26)
	sym_state0 = sym_state1
	sym_state1 = s1
	if browser == "chrome":
		calc = sym_state0
	else:
		calc = sym_state0 + sym_state1

	condition = Bool("c%d" % int(generated * random.random()))
	if browser == "chrome":
		impl = Implies(condition, LShR(calc, 12) == int(generated))
	elif browser == "firefox" or browser == "safari":
		# Firefox and Safari save an extra bit
		impl = Implies(condition, (calc & 0x1FFFFFFFFFFFFF) == int(generated))
	else:
		raise ValueError(f"invalid browser {browser}")
	slvr.add(impl)
	return sym_state0, sym_state1, [condition]


def reverse17(val):
	return val ^ (val >> 17) ^ (val >> 34) ^ (val >> 51)


def reverse23(val):
	return (val ^ (val << 23) ^ (val << 46)) & MASK


def xs128p_backward(state0, state1, browser):
	prev_state1 = state0
	prev_state0 = state1 ^ (state0 >> 26)
	prev_state0 = prev_state0 ^ state0
	prev_state0 = reverse17(prev_state0)
	prev_state0 = reverse23(prev_state0)
	# this is only called from an if chrome
	# but let"s be safe in case someone copies it out
	if browser == "chrome":
		generated = prev_state0
	else:
		generated = (prev_state0 + prev_state1) & MASK
	return prev_state0, prev_state1, generated


# Firefox nextDouble():
# (rand_uint64 & ((1 << 53) - 1)) / (1 << 53)
# Chrome nextDouble():
# (state0 | 0x3FF0000000000000) - 1.0
# Safari weakRandom.get():
# (rand_uint64 & ((1 << 53) - 1) * (1.0 / (1 << 53)))
def to_double(out, browser):
	if browser == "chrome":
		double_bits = (out >> 12) | 0x3FF0000000000000
		return struct.unpack("d", struct.pack("<Q", double_bits))[0] - 1
	elif browser == "firefox":
		return float(out & 0x1FFFFFFFFFFFFF) / (0x1 << 53)
	elif browser == "safari":
		return float(out & 0x1FFFFFFFFFFFFF) * (1.0 / (0x1 << 53))
	else:
		raise ValueError(f"invalid browser {browser}")


def from_double(double, browser):
	if browser == "chrome":
		return struct.unpack("<Q", struct.pack("d", double + 1))[0] & (MASK >> 12)
	elif browser == "firefox":
		return double * (0x1 << 53)
	elif browser == "safari":
		return double / (1.0 / (1 << 53))
	else:
		raise ValueError(f"invalid browser {browser}")


def get_state(doubles, browser):
	if browser == "node":
		browser = "chrome"
	elif browser not in {"chrome", "firefox", "safari"}:
		raise ValueError(f"invalid browser {browser}")
	if browser == "chrome":
		doubles = doubles[::-1]

	# from the doubles, generate known piece of the original uint64
	generated = [from_double(double, browser) for double in doubles]

	# setup symbolic state for xorshift128+
	ostate0, ostate1 = BitVecs("ostate0 ostate1", 64)
	sym_state0 = ostate0
	sym_state1 = ostate1
	solver = Solver()
	conditions = []

	# run symbolic xorshift128+ algorithm for three iterations
	# using the recovered numbers as constraints
	for val in generated:
		sym_state0, sym_state1, ret_conditions = sym_xs128p(
			solver, sym_state0, sym_state1, val, browser
		)
		conditions += ret_conditions
	if solver.check(conditions) == sat:
		# get a solved state
		m = solver.model()
		state0 = m[ostate0].as_long()
		state1 = m[ostate1].as_long()
		solver.add(Or(ostate0 != m[ostate0], ostate1 != m[ostate1]))
		if solver.check(conditions) == sat:
			print("WARNING: multiple solutions found! use more doubles!")
		return state0, state1
	else:
		raise ValueError("unsat model")


def predict_rands(doubles, browser):
	if browser == "node":
		browser = "chrome"
	elif browser not in {"chrome", "firefox", "safari"}:
		raise ValueError(f"invalid browser {browser}")
	state0, state1 = get_state(doubles, browser)
	# generate random numbers from recovered state
	while True:
		if browser == "chrome":
			state0, state1, out = xs128p_backward(state0, state1, browser)
			out = state0 & MASK
		else:
			state0, state1, out = xs128p(state0, state1, browser)

		yield to_double(out, browser)


def main():
	import itertools  # noqa: PLC0415
	import sys  # noqa: PLC0415

	if len(sys.argv) < 4:
		print("Usage: xs128p.py browser num doubles...")
		sys.exit(1)
	browser = sys.argv[1]
	n = int(sys.argv[2])
	doubles = list(map(float, sys.argv[3:]))
	for i in itertools.islice(predict_rands(doubles, browser), 0, n):
		print(i)


if __name__ == "__main__":
	main()
