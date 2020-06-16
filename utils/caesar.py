#!/usr/bin/env python3
import sys

from utils.crypto.classical import caesar_all

alphabet_only = len(sys.argv) == 1 or sys.argv[1] != "-a"
s = sys.stdin.read().strip()
print("\n".join(caesar_all(s,alphabet_only)))
