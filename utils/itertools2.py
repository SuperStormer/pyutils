# pylint: disable=all
"""from the itertools recipes section of https://docs.python.org/3/library/itertools.html"""

import collections
import math
import operator
from itertools import (
	chain,
	combinations,
	count,
	cycle,
	filterfalse,
	groupby,
	islice,
	repeat,
	starmap,
	tee,
	zip_longest,
)


def take(n, iterable):
	"Return first n items of the iterable as a list"
	return list(islice(iterable, n))


def prepend(value, iterable):
	"Prepend a single value in front of an iterable"
	# prepend(1, [2, 3, 4]) --> 1 2 3 4
	return chain([value], iterable)


def tabulate(function, start=0):
	"Return function(0), function(1), ..."
	return map(function, count(start))


def tail(n, iterable):
	"Return an iterator over the last n items"
	# tail(3, 'ABCDEFG') --> E F G
	return iter(collections.deque(iterable, maxlen=n))


def consume(iterator, n=None):
	"Advance the iterator n-steps ahead. If n is None, consume entirely."
	# Use functions that consume iterators at C speed.
	if n is None:
		# feed the entire iterator into a zero-length deque
		collections.deque(iterator, maxlen=0)
	else:
		# advance to the empty slice starting at position n
		next(islice(iterator, n, n), None)


def nth(iterable, n, default=None):
	"Returns the nth item or a default value"
	return next(islice(iterable, n, None), default)


def all_equal(iterable):
	"Returns True if all the elements are equal to each other"
	g = groupby(iterable)
	return next(g, True) and not next(g, False)


def quantify(iterable, pred=bool):
	"Count how many times the predicate is True"
	return sum(map(pred, iterable))


def ncycles(iterable, n):
	"Returns the sequence elements n times"
	return chain.from_iterable(repeat(tuple(iterable), n))


def batched(iterable, n):
	"Batch data into tuples of length n. The last batch may be shorter."
	# batched('ABCDEFG', 3) --> ABC DEF G
	if n < 1:
		raise ValueError("n must be at least one")
	it = iter(iterable)
	while batch := tuple(islice(it, n)):
		yield batch


def grouper(iterable, n, *, incomplete="fill", fillvalue=None):
	"Collect data into non-overlapping fixed-length chunks or blocks"
	# grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
	# grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
	# grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
	args = [iter(iterable)] * n
	if incomplete == "fill":
		return zip_longest(*args, fillvalue=fillvalue)
	if incomplete == "strict":
		return zip(*args, strict=True)
	if incomplete == "ignore":
		return zip(*args)
	else:
		raise ValueError("Expected fill, strict, or ignore")


def sumprod(vec1, vec2):
	"Compute a sum of products."
	return sum(starmap(operator.mul, zip(vec1, vec2, strict=True)))


def sum_of_squares(it):
	"Add up the squares of the input values."
	# sum_of_squares([10, 20, 30]) -> 1400
	return sumprod(*tee(it))


def transpose(it):
	"Swap the rows and columns of the input."
	# transpose([(1, 2, 3), (11, 22, 33)]) --> (1, 11) (2, 22) (3, 33)
	return zip(*it, strict=True)


def matmul(m1, m2):
	"Multiply two matrices."
	# matmul([(7, 5), (3, 5)], [[2, 5], [7, 9]]) --> (49, 80), (41, 60)
	n = len(m2[0])
	return batched(starmap(sumprod, product(m1, transpose(m2))), n)


def convolve(signal, kernel):
	# See:  https://betterexplained.com/articles/intuitive-convolution/
	# convolve(data, [0.25, 0.25, 0.25, 0.25]) --> Moving average (blur)
	# convolve(data, [1, -1]) --> 1st finite difference (1st derivative)
	# convolve(data, [1, -2, 1]) --> 2nd finite difference (2nd derivative)
	kernel = tuple(kernel)[::-1]
	n = len(kernel)
	window = collections.deque([0], maxlen=n) * n
	for x in chain(signal, repeat(0, n - 1)):
		window.append(x)
		yield sumprod(kernel, window)


def polynomial_from_roots(roots):
	"""Compute a polynomial's coefficients from its roots.

	(x - 5) (x + 4) (x - 3)  expands to:   x³ -4x² -17x + 60
	"""
	# polynomial_from_roots([5, -4, 3]) --> [1, -4, -17, 60]
	expansion = [1]
	for r in roots:
		expansion = convolve(expansion, (1, -r))
	return list(expansion)


def polynomial_eval(coefficients, x):
	"""Evaluate a polynomial at a specific value.

	Computes with better numeric stability than Horner's method.
	"""
	# Evaluate x³ -4x² -17x + 60 at x = 2.5
	# polynomial_eval([1, -4, -17, 60], x=2.5) --> 8.125
	n = len(coefficients)
	if n == 0:
		return x * 0  # coerce zero to the type of x
	powers = map(pow, repeat(x), reversed(range(n)))
	return sumprod(coefficients, powers)


def iter_index(iterable, value, start=0):
	"Return indices where a value occurs in a sequence or iterable."
	# iter_index('AABCADEAF', 'A') --> 0 1 4 7
	try:
		seq_index = iterable.index
	except AttributeError:
		# Slow path for general iterables
		it = islice(iterable, start, None)
		i = start - 1
		try:
			while True:
				yield (i := i + operator.indexOf(it, value) + 1)
		except ValueError:
			pass
	else:
		# Fast path for sequences
		i = start - 1
		try:
			while True:
				yield (i := seq_index(value, i + 1))
		except ValueError:
			pass


def sieve(n):
	"Primes less than n"
	# sieve(30) --> 2 3 5 7 11 13 17 19 23 29
	data = bytearray((0, 1)) * (n // 2)
	data[:3] = 0, 0, 0
	limit = math.isqrt(n) + 1
	for p in compress(range(limit), data):
		data[p * p : n : p + p] = bytes(len(range(p * p, n, p + p)))
	data[2] = 1
	return iter_index(data, 1) if n > 2 else iter([])


def factor(n):
	"Prime factors of n."
	# factor(99) --> 3 3 11
	for prime in sieve(math.isqrt(n) + 1):
		while True:
			quotient, remainder = divmod(n, prime)
			if remainder:
				break
			yield prime
			n = quotient
			if n == 1:
				return
	if n > 1:
		yield n


def flatten(list_of_lists):
	"Flatten one level of nesting"
	return chain.from_iterable(list_of_lists)


def repeatfunc(func, times=None, *args):
	"""Repeat calls to func with specified arguments.

	Example:  repeatfunc(random.random)
	"""
	if times is None:
		return starmap(func, repeat(args))
	return starmap(func, repeat(args, times))


def triplewise(iterable):
	"Return overlapping triplets from an iterable"
	# triplewise('ABCDEFG') --> ABC BCD CDE DEF EFG
	for (a, _), (b, c) in pairwise(pairwise(iterable)):
		yield a, b, c


def sliding_window(iterable, n):
	# sliding_window('ABCDEFG', 4) --> ABCD BCDE CDEF DEFG
	it = iter(iterable)
	window = collections.deque(islice(it, n), maxlen=n)
	if len(window) == n:
		yield tuple(window)
	for x in it:
		window.append(x)
		yield tuple(window)


def roundrobin(*iterables):
	"roundrobin('ABC', 'D', 'EF') --> A D E B F C"
	# Recipe credited to George Sakkis
	num_active = len(iterables)
	nexts = cycle(iter(it).__next__ for it in iterables)
	while num_active:
		try:
			for next in nexts:
				yield next()
		except StopIteration:
			# Remove the iterator we just exhausted from the cycle.
			num_active -= 1
			nexts = cycle(islice(nexts, num_active))


def partition(pred, iterable):
	"Use a predicate to partition entries into false entries and true entries"
	# partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
	t1, t2 = tee(iterable)
	return filterfalse(pred, t1), filter(pred, t2)


def before_and_after(predicate, it):
	"""Variant of takewhile() that allows complete
	access to the remainder of the iterator.

	>>> it = iter("ABCdEfGhI")
	>>> all_upper, remainder = before_and_after(str.isupper, it)
	>>> "".join(all_upper)
	'ABC'
	>>> "".join(remainder)  # takewhile() would lose the 'd'
	'dEfGhI'

	Note that the first iterator must be fully
	consumed before the second iterator can
	generate valid results.
	"""
	it = iter(it)
	transition = []

	def true_iterator():
		for elem in it:
			if predicate(elem):
				yield elem
			else:
				transition.append(elem)
				return

	def remainder_iterator():
		yield from transition
		yield from it

	return true_iterator(), remainder_iterator()


def subslices(seq):
	"Return all contiguous non-empty subslices of a sequence"
	# subslices('ABCD') --> A AB ABC ABCD B BC BCD C CD D
	slices = starmap(slice, combinations(range(len(seq) + 1), 2))
	return map(operator.getitem, repeat(seq), slices)


def powerset(iterable):
	"powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
	s = list(iterable)
	return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def unique_everseen(iterable, key=None):
	"List unique elements, preserving order. Remember all elements ever seen."
	# unique_everseen('AAAABBBCCDAABBB') --> A B C D
	# unique_everseen('ABBcCAD', str.lower) --> A B c D
	seen = set()
	if key is None:
		for element in filterfalse(seen.__contains__, iterable):
			seen.add(element)
			yield element
		# For order preserving deduplication,
		# a faster but non-lazy solution is:
		#     yield from dict.fromkeys(iterable)
	else:
		for element in iterable:
			k = key(element)
			if k not in seen:
				seen.add(k)
				yield element
		# For use cases that allow the last matching element to be returned,
		# a faster but non-lazy solution is:
		#      t1, t2 = tee(iterable)
		#      yield from dict(zip(map(key, t1), t2)).values()


def unique_justseen(iterable, key=None):
	"List unique elements, preserving order. Remember only the element just seen."
	# unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
	# unique_justseen('ABBcCAD', str.lower) --> A B c A D
	return map(next, map(operator.itemgetter(1), groupby(iterable, key)))


def iter_except(func, exception, first=None):
	"""Call a function repeatedly until an exception is raised.

	Converts a call-until-exception interface to an iterator interface.
	Like builtins.iter(func, sentinel) but uses an exception instead
	of a sentinel to end the loop.

	Examples:
	    iter_except(functools.partial(heappop, h), IndexError)   # priority queue iterator
	    iter_except(d.popitem, KeyError)                         # non-blocking dict iterator
	    iter_except(d.popleft, IndexError)                       # non-blocking deque iterator
	    iter_except(q.get_nowait, Queue.Empty)                   # loop over a producer Queue
	    iter_except(s.pop, KeyError)                             # non-blocking set iterator

	"""
	try:
		if first is not None:
			yield first()  # For database APIs needing an initial cast to db.first()
		while True:
			yield func()
	except exception:
		pass


def first_true(iterable, default=False, pred=None):
	"""Returns the first true value in the iterable.

	If no true value is found, returns *default*

	If *pred* is not None, returns the first item
	for which pred(item) is true.

	"""
	# first_true([a,b,c], x) --> a or b or c or x
	# first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
	return next(filter(pred, iterable), default)


def nth_combination(iterable, r, index):
	"Equivalent to list(combinations(iterable, r))[index]"
	pool = tuple(iterable)
	n = len(pool)
	c = math.comb(n, r)
	if index < 0:
		index += c
	if index < 0 or index >= c:
		raise IndexError
	result = []
	while r:
		c, n, r = c * r // n, n - 1, r - 1
		while index >= c:
			index -= c
			c, n = c * (n - r) // n, n - 1
		result.append(pool[-1 - n])
	return tuple(result)
