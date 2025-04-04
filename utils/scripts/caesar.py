#!/usr/bin/env python3
import argparse
import sys

from utils.crypto.classical import caesar_all


def main():
	parser = argparse.ArgumentParser(description="Try all caesar shifts on a string.")
	parser.add_argument("string", nargs="?", help="string to shift")
	parser.add_argument(
		"-s", "--shift", help="prefix encoded string with shift", action="store_true"
	)
	parser.add_argument(
		"-a", "--all", help="try all ascii values as shift", action="store_true"
	)
	args = parser.parse_args()
	alphabet_only = not args.all
	s = args.string
	if s is None:
		s = sys.stdin.read().strip()
	print(
		"\n".join(
			(f"{c.shift}:" if args.shift else "") + c.text
			for c in caesar_all(s, alphabet_only=alphabet_only)
		)
	)


if __name__ == "__main__":
	main()
