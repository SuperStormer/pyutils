#!/usr/bin/env python3
import sys

from utils.ctftools import caesar

alphabet_only = len(sys.argv) == 1
s = sys.stdin.read().strip()
print("\n".join(caesar(s,alphabet_only)))
