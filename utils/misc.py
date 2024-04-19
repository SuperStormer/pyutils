def is_palindrome(s):
	return s == "".join(reversed(s))


def rotations(n):
	for i in range(len(n)):
		yield n[i:] + n[:i]


def num_to_word(n):
	ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
	teens = [
		"ten",
		"eleven",
		"twelve",
		"thirteen",
		"fourteen",
		"fifteen",
		"sixteen",
		"seventeen",
		"eighteen",
		"nineteen",
	]
	tens = [
		"",
		"",
		"twenty",
		"thirty",
		"forty",
		"fifty",
		"sixty",
		"seventy",
		"eighty",
		"ninety",
	]
	prefix = ""
	if n == 0:
		return "zero"
	if n % 1000 == 0:
		return prefix + ones[n // 1000] + " thousand"
	if n > 1000:
		prefix += ones[n // 1000] + " thousand and "
		n = n % 1000
	if n % 100 == 0:
		return prefix + ones[n // 100] + " hundred"
	if n > 100:
		prefix += ones[n // 100] + " hundred and "
		n = n % 100
	if n < 10:
		return prefix + ones[n]
	if n < 20:
		return prefix + teens[n - 10]
	return prefix + tens[n // 10] + " " + ones[n % 10]
