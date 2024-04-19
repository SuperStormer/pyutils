#!/usr/bin/env python3
import sys
from dataclasses import dataclass

import requests

INDEX_URL = "http://www.factordb.com/index.php"
API_URL = "http://www.factordb.com/api"


@dataclass
class Result:
	status: str
	factors: list[int]


def fetch_result(n: int) -> Result:
	# The first request is necessary if the number isn't in the DB yet, no idea why
	requests.get(INDEX_URL, params={"query": str(n)}, timeout=10)
	resp = requests.get(API_URL, params={"query": str(n)}, timeout=10).json()
	return Result(
		resp["status"],
		[int(factor[0]) for factor in resp["factors"] for _ in range(factor[1])],
	)


def factors(n: int) -> list[int]:
	return fetch_result(n).factors


if __name__ == "__main__":
	print(factors(int(sys.argv[1])))
