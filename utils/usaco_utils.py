#TODO clean this up
import itertools
import math
import string
from numbers import Real
from functools import reduce
from typing import TypeVar, List, Callable, Generator, Sequence, Union, Set, Any, Tuple, Reversible, Iterator

T = TypeVar("T")

def merge_sequence(sequence: Sequence[T], merge_func: Callable[[T, T], T]) -> Generator[T, None,
	None]:
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
	original_sequence: Union[Sequence[T], Set[T]],
	merge_func: Callable[[T, T], T],
	key_func: Callable[[T], Any] = lambda x: x
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

def palindromes(length: int, possible_chars=string.ascii_letters) -> Iterator[str]:
	combos = map("".join, itertools.product(possible_chars, repeat=length // 2))
	if length % 2 == 1:  #odd num of digits
		return (
			combo + str(middle_char) + "".join(reversed(combo)) for combo in combos
			for middle_char in possible_chars
		)
	else:
		return (combo + "".join(reversed(combo)) for combo in combos)

def palindrome_nums(length: int):
	return map(int, palindromes(length, possible_chars=string.digits))
