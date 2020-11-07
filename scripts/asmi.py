#!/usr/bin/env python3
from keystone import Ks, KS_ARCH_X86, KS_MODE_64
from keystone.keystone import KsError
from utils.hazmat.shellcode import run_shellcode
import re
import readline
import ctypes
import traceback
#from https://gist.github.com/amtal/c457176af7f8770e0ad519aadc86013c/
REG_NAMES = [
	"rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"
]
#ignore rbp and rsp

class AsmRepl():
	def __init__(self, to_print={"regs"}):
		self.regs = {reg: 0 for reg in REG_NAMES}
		self.ks = Ks(KS_ARCH_X86, KS_MODE_64)
		self.libc = ctypes.CDLL("libc.so.6")
		self.to_print = to_print
	
	def loop(self):
		while True:
			inp = input("asmi> ")
			if inp.startswith("!"):
				try:
					print(eval(inp[1:], self.regs.copy(), {}))
				except Exception:
					traceback.print_exc()
			elif inp.startswith("~"):
				inp = inp[1:]
				if inp.startswith("-") and inp[1:] in self.to_print:
					self.to_print.remove(inp[1:])
				else:
					self.to_print.add(inp)
			else:
				self.run(inp)
	
	def _get_libc_address(self, func):
		return ctypes.cast(self.libc[func], ctypes.c_void_p).value
	
	def run(self, asm):
		reg_save = (ctypes.c_uint64 * len(self.regs))()
		reg_save_addr = ctypes.cast(reg_save, ctypes.c_void_p).value
		stack = (ctypes.c_uint64 * 128)()
		stack_addr = ctypes.cast(stack, ctypes.c_void_p).value
		rsp_save = (ctypes.c_uint64 * 1)()
		rsp_save_addr = ctypes.cast(rsp_save, ctypes.c_void_p).value
		rbp_save = (ctypes.c_uint64 * 1)()
		rbp_save_addr = ctypes.cast(rbp_save, ctypes.c_void_p).value
		#1. set rsp and rbp to the stack location and save the original rsp and rbp
		#2. mov all of the saved regs to the right spot
		#3. run the user input
		#4. save all the regs in the buffer
		#5. mov the saved rsp and rbp to rsp and rbp
		try:
			asm = re.sub(r"<(\w+)>", lambda m: str(self._get_libc_address(m.group(1))), asm)
		except IndexError as e:
			print(e)
			return
		asm = (
			f"mov rbx, rsp; mov rcx, rbp; mov rbp, {stack_addr+(len(stack))*8}; mov rsp, rbp;" +
			f"mov rax, rbx; mov [{rsp_save_addr}], rax; mov rax, rcx; mov [{rbp_save_addr}], rax; "
			+ "; ".join(f"mov {name}, {val}"
			for name, val in self.regs.items()) + "; " + asm + "; " + "; ".join(
			f"mov rax, {reg}; mov [{reg_save_addr+i*8}], rax" for i, reg in enumerate(self.regs)
			) +
			f"; mov rax, [{rsp_save_addr}]; mov rsp, rax; mov rax, [{rbp_save_addr}]; mov rbp, rax; ret;"
		)
		if "asm" in self.to_print:
			print(asm)
		try:
			code = self.ks.asm(asm, as_bytes=True)[0]
			if "code" in self.to_print:
				print(code)
		except KsError as e:
			print(e)
			return
		run_shellcode(code)
		if "stack" in self.to_print:
			print(list(stack))
		self.regs = {reg: val for reg, val in zip(REG_NAMES, reg_save)}
		if "regs" in self.to_print:
			print(self.regs)

if __name__ == "__main__":
	import sys
	args = {"regs"}
	for arg in sys.argv[1:]:
		if arg.startswith("-") and arg[1:] in args:
			args.remove(arg[1:])
		else:
			args.add(arg)
	AsmRepl(args).loop()
