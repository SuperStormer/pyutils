#pylint: disable=all
""" from the itertools recipes section of https://docs.python.org/3/library/itertools.html"""
import operator
import collections
import random
from itertools import (
	chain, combinations, count, cycle, filterfalse, groupby, islice, repeat, starmap, tee,
	zip_longest
)

def take(n, iterable):
	"Return first n items of the iterable as a list"
	return list(islice(iterable, n))

def prepend(value, iterator):
	"Prepend a single value in front of an iterator"
	# prepend(1, [2, 3, 4]) -> 1 2 3 4
	return chain([value], iterator)

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
	"Count how many times the predicate is true"
	return sum(map(pred, iterable))

def pad_none(iterable):
	"""Returns the sequence elements and then returns None indefinitely.

    Useful for emulating the behavior of the built-in map() function.
    """
	return chain(iterable, repeat(None))

def ncycles(iterable, n):
	"Returns the sequence elements n times"
	return chain.from_iterable(repeat(tuple(iterable), n))

def dotproduct(vec1, vec2):
	return sum(map(operator.mul, vec1, vec2))

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
		yield sum(map(operator.mul, kernel, window))

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

def grouper(iterable, n, *, incomplete='fill', fillvalue=None):
	"Collect data into non-overlapping fixed-length chunks or blocks"
	# grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
	# grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
	# grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
	args = [iter(iterable)] * n
	if incomplete == 'fill':
		return zip_longest(*args, fillvalue=fillvalue)
	if incomplete == 'strict':
		return zip(*args, strict=True)
	if incomplete == 'ignore':
		return zip(*args)
	else:
		raise ValueError('Expected fill, strict, or ignore')

def triplewise(iterable):
	"Return overlapping triplets from an iterable"
	# triplewise('ABCDEFG') -> ABC BCD CDE DEF EFG
	for (a, _), (b, c) in pairwise(pairwise(iterable)):
		yield a, b, c

def sliding_window(iterable, n):
	# sliding_window('ABCDEFG', 4) -> ABCD BCDE CDEF DEFG
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
	""" Variant of takewhile() that allows complete
        access to the remainder of the iterator.

        >>> it = iter('ABCdEfGhI')
        >>> all_upper, remainder = before_and_after(str.isupper, it)
        >>> ''.join(all_upper)
        'ABC'
        >>> ''.join(remainder)     # takewhile() would lose the 'd'
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
	# unique_everseen('ABBCcAD', str.lower) --> A B C D
	seen = set()
	seen_add = seen.add
	if key is None:
		for element in filterfalse(seen.__contains__, iterable):
			seen_add(element)
			yield element
	else:
		for element in iterable:
			k = key(element)
			if k not in seen:
				seen_add(k)
				yield element

def unique_justseen(iterable, key=None):
	"List unique elements, preserving order. Remember only the element just seen."
	# unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
	# unique_justseen('ABBCcAD', str.lower) --> A B C A D
	return map(next, map(operator.itemgetter(1), groupby(iterable, key)))

def iter_except(func, exception, first=None):
	""" Call a function repeatedly until an exception is raised.

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

def random_product(*args, repeat=1):
	"Random selection from itertools.product(*args, **kwds)"
	pools = [tuple(pool) for pool in args] * repeat
	return tuple(map(random.choice, pools))

def random_permutation(iterable, r=None):
	"Random selection from itertools.permutations(iterable, r)"
	pool = tuple(iterable)
	r = len(pool) if r is None else r
	return tuple(random.sample(pool, r))

def random_combination(iterable, r):
	"Random selection from itertools.combinations(iterable, r)"
	pool = tuple(iterable)
	n = len(pool)
	indices = sorted(random.sample(range(n), r))
	return tuple(pool[i] for i in indices)

def random_combination_with_replacement(iterable, r):
	"Random selection from itertools.combinations_with_replacement(iterable, r)"
	pool = tuple(iterable)
	n = len(pool)
	indices = sorted(random.choices(range(n), k=r))
	return tuple(pool[i] for i in indices)

def nth_combination(iterable, r, index):
	"Equivalent to list(combinations(iterable, r))[index]"
	pool = tuple(iterable)
	n = len(pool)
	if r < 0 or r > n:
		raise ValueError
	c = 1
	k = min(r, n - r)
	for i in range(1, k + 1):
		c = c * (n - k + i) // i
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
