#!/usr/bin/env python3
from typing import List
from dataclasses import dataclass
import requests
import sys
URL = "http://www.factordb.com/api"

@dataclass
class Result:
	status: str
	factors: List[int]

def fetch_result(n: int) -> Result:
	resp = requests.get(URL, params={"query": str(n)}).json()
	return Result(
		resp["status"], [int(factor[0]) for factor in resp["factors"] for _ in range(factor[1])]
	)

def factors(n: int) -> List[int]:
	return fetch_result(n).factors

if __name__ == "__main__":
	print(factors(sys.argv[1]))
