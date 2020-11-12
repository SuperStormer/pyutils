#!/usr/bin/env python3
from abc import ABC, abstractmethod
import subprocess
import socket
import time
import os
import select

class Connection(ABC):
	def __init__(self):
		self.buffer = b""
	
	@abstractmethod
	def recv_raw(self, timeout):
		pass
	
	def recv(self, timeout=0.2) -> str:
		self.buffer += self.recv_raw(timeout)
		buffer = self.buffer
		self.buffer = b""
		return buffer.decode("utf-8")
	
	def recvline(self, timeout=0.2) -> str:
		start_time = time.time()
		while b"\n" not in self.buffer and time.time() < start_time + timeout:
			self.buffer += self.recv_raw(timeout)
		i = self.buffer.find(b"\n")
		buffer = self.buffer[:i + 1]
		self.buffer = self.buffer[i + 1:]
		return buffer.decode("utf-8")
	
	def recvlines(self, n):
		return [self.recvline() for _ in range(n)]
	
	@abstractmethod
	def send(self, s: str):
		pass
	
	def sendline(self, s: str = ""):
		self.send(s + "\n")
	
	def sendlines(self, l: list):
		for s in l:
			self.sendline(s)
	
	@abstractmethod
	def __enter__(self):
		pass
	
	@abstractmethod
	def __exit__(self, e_type, e_value, e_traceback):
		pass

class Process(Connection):
	def __init__(self, executable: str, args: list = None, **kwargs):
		if args is None:
			args = []
		super().__init__()
		self.executable = executable
		self.args = args
		self.process = subprocess.Popen(
			[self.executable] + self.args,
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			**kwargs
		)
	
	def recv_raw(self, timeout):
		if self.process.poll() is not None:
			raise OSError("Process has ended")
		select.select([self.process.stdout], [], [], timeout)
		return os.read(self.process.stdout.fileno(), 1024)
	
	def send(self, s: str):
		self.process.stdin.write(s.encode("utf-8"))
		self.process.stdin.flush()
	
	def __enter__(self):
		self.process.__enter__()
		return self
	
	def __exit__(self, e_type, e_value, e_traceback):
		self.process.__exit__(e_type, e_value, e_traceback)

class Socket(Connection):
	def __init__(self, host: str, port: int):
		super().__init__()
		self.host = host
		self.port = port
		self.read_size = 1024
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	def recv_raw(self, timeout):
		if not select.select([self.socket], [], [], timeout):
			raise OSError("Socket is closed")
		out = self.socket.recv(self.read_size)
		if not out:
			raise OSError("Socket is closed")
		return out
	
	def send(self, s: str):
		self.socket.sendall(s.encode("utf-8"))
	
	def __enter__(self):
		self.socket.__enter__()
		self.socket.connect((self.host.encode("utf-8"), self.port))
		return self
	
	def __exit__(self, e_type, e_value, e_traceback):
		self.socket.__exit__(e_type, e_value, e_traceback)

class PwntoolsWrapper(Connection):
	def __init__(self, tube):
		super().__init__()
		self.tube = tube
	
	def recv_raw(self, timeout):
		return self.tube.recv(1024, timeout).decode("utf-8")
	
	def send(self, s: str):
		self.tube.sendall(s)
	
	def __enter__(self):
		pass
	
	def __exit__(self, e_type, e_value, e_traceback):
		pass
