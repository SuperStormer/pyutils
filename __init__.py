from itertools import zip_longest
import math
from typing import TypeVar, List, Callable, Generator, Sequence, Union, Set
T = TypeVar("T")

def merge_sequence(sequence: Sequence[T], merge_func: Callable[[T, T], T]) -> Generator[T, None, None]:
	for element1, element2 in zip_longest(sequence[::2], sequence[1::2]):
		if not element1:
			yield element1
			continue
		merged_element = merge_func(element1, element2)
		if merged_element:
			yield merged_element
		else:
			yield element1
			yield element2

def optional_reduce(original_sequence: Union[Sequence[T], Set[T]], merge_func: Callable[[T, T], T]) -> List[T]:
	sorted_sequence = sorted(original_sequence)
	new_sequence = min(
		list(merge_sequence(sorted_sequence, merge_func)),
		list(merge_sequence(sorted_sequence[1:], merge_func)) + [
		sorted_sequence[0],
		],
		key=lambda x: len(x)
	)
	if len(new_sequence) < len(original_sequence):
		return optional_reduce(new_sequence, merge_func)
	return sorted_sequence

def int_to_base(
	integer: int,
	base: int,
	alphabet=[
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
	'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
	]
) -> str:
	base_str = ""
	for i in range(math.floor(math.log(integer, base)), -1, -1):
		base_str += alphabet[integer // (base**i)]
		integer = integer % (base**i)
	return base_str

def is_palindrome(string: str) -> bool:
	return string == "".join(reversed(string))
