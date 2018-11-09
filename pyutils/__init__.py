import itertools
import math
from numbers import Real, Integral
from functools import reduce, lru_cache
from typing import TypeVar, List, Callable, Generator, Sequence, Union, Set, Any, Tuple, Reversible, Iterator
from inspect import signature
from string import digits, ascii_uppercase
T = TypeVar("T")

def merge_sequence(sequence: Sequence[T], merge_func: Callable[[T, T], T]) -> Generator[T, None, None]:
	for element1, element2 in itertools.zip_longest(sequence[::2], sequence[1::2]):
		if not element2:
			yield element1
			continue
		merged_element = merge_func(element1, element2)
		if merged_element:
			yield merged_element
		else:
			yield element1
			yield element2

def optional_reduce(
	original_sequence: Union[Sequence[T], Set[T]], merge_func: Callable[[T, T], T], key_func: Callable[[T], Any] = lambda x: x
) -> List[T]:
	sorted_sequence = sorted(original_sequence, key=key_func)
	new_sequence = min(
		list(merge_sequence(sorted_sequence, merge_func)),
		list(merge_sequence(sorted_sequence[1:], merge_func)) + [
		sorted_sequence[0],
		],
		key=len
	)
	if len(new_sequence) < len(original_sequence):
		return optional_reduce(new_sequence, merge_func)
	return sorted_sequence

_alphabet = tuple(digits + ascii_uppercase)

@lru_cache(maxsize=None)
def int_to_base(
	integer: int,
	base: int,
) -> str:
	base_str = ""
	for i in range(math.floor(math.log(integer, base)), -1, -1):
		base_str += _alphabet[integer // (base**i)]
		integer = integer % (base**i)
	return base_str

@lru_cache(maxsize=None)
def is_palindrome(string: str) -> bool:
	return string == "".join(reversed(string))

E = TypeVar("E")

def pairings(sequence: List[E]) -> Generator[List[Tuple[E, E]], None, None]:
	if len(sequence) < 2:
		yield []
		return
	if len(sequence) % 2 == 1:
		for i in range(len(sequence)):
			yield from pairings(sequence[0:i] + sequence[i + 1:])
	else:
		first_element = sequence[0]
		for i, element in enumerate(sequence[1:], start=1):
			pair = (first_element, element)
			yield from ([pair] + rest for rest in pairings(sequence[1:i] + sequence[i + 1:]))

def round_half_up(num: Real) -> int:
	return math.floor(num + 0.5)

def clamp(num: Real, min_num: Real, max_num: Real) -> Real:
	return max(min_num, min(max_num, num))

A = TypeVar("A")

def reduce_right(func: Callable[[A, A], A], sequence: Reversible, accumulator: A) -> A:
	return reduce(lambda x, y: func(y, x), reversed(sequence), accumulator)

def compose(*funcs):
	def composed_func(args):
		return reduce_right(lambda x, func: func(x), funcs, args)
	
	return composed_func

def flip(func: Callable, *args):
	return func(args[::-1])

@lru_cache(maxsize=None)
def is_prime(num):
	if num == 2:
		return True
	if num == 1 or num == 0:
		return False
	if num % 2 == 0:
		return False
	for i in range(2, math.floor(math.sqrt(num)) + 1):
		if num % i == 0:
			return False
	return True

def palindromes(digits: int) -> Iterator[int]:
	combos = itertools.product(range(0, 10), repeat=digits // 2)
	str_combos = ("".join(map(str, combo)) for combo in combos)
	if digits % 2 == 1:  #odd num of digits
		return (
			int(combo + str(middle_digit) + "".join(reversed(combo))) for combo in str_combos for middle_digit in range(0, 10)
		)
	else:
		return (int(combo + "".join(reversed(combo))) for combo in str_combos)

@lru_cache(maxsize=None)
def fibonnaci(n: int) -> int:
	if n < 2:
		return n
	return fibonnaci(n - 1) + fibonnaci(n - 2)

def fibonnaci_gen(num: int) -> Generator[int, None, None]:
	a = 1
	b = 1
	yield 1
	yield 1
	for _ in range(num - 2):
		c = a + b
		yield c
		a, b = b, c
