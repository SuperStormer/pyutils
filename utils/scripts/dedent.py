#!/usr/bin/env python3
import sys
import textwrap


def main():
	print(textwrap.dedent(sys.stdin.read()))


if __name__ == "__main__":
	main()
