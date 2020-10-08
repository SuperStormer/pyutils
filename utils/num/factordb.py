#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from typing import List

import requests

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
	print(factors(int(sys.argv[1])))
