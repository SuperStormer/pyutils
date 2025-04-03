#!/usr/bin/env python3
import ctypes
import re
import readline
import textwrap
import traceback
import typing
from pathlib import Path

from keystone import KS_ARCH_X86, KS_MODE_64, Ks, KsError

from utils.hazmat.misc import get_addr
from utils.hazmat.shellcode import run_shellcode

# ignore rbp and rsp
REG_NAMES = [
	"rax",
	"rbx",
	"rcx",
	"rdx",
	"rsi",
	"rdi",
	"r8",
	"r9",
	"r10",
	"r11",
	"r12",
	"r13",
	"r14",
	"r15",
]
FLAG_NAMES = {
	0: ("CF", "carry"),
	2: ("PF", "parity"),
	4: ("AF", "adjust"),
	6: ("ZF", "zero"),
	7: ("SF", "sign"),
	8: ("TF", "trap"),
	9: ("IF", "interrupt"),
	10: ("DF", "direction"),
	11: ("OF", "overflow"),
	14: ("NT", "nested_task"),
	16: ("RF", "resume"),
	17: ("VM", "virtual_x86"),
	18: ("AC", "alignment_check"),
	19: ("VIF", "virtual_interrupt"),
	20: ("VIP", "virtual_interrupt_pending"),
	21: ("ID", "cpuid"),
}


def create_array(length):
	array = (ctypes.c_uint64 * length)()
	return (array, typing.cast(int, get_addr(array)))


def create_ptr(val=0):
	ptr = ctypes.pointer(ctypes.c_uint64(val))
	return (ptr, get_addr(ptr))


class AsmRepl:
	def __init__(self, to_print=None, stack_size=128, history_file="~/.iasm_history"):
		if to_print is None:
			self.to_print = {"regs"}
		else:
			self.to_print = to_print
		self.stack_size = stack_size
		self.history_file = Path(history_file).expanduser()

		self.regs = {reg: 0 for reg in REG_NAMES}
		self.ks = Ks(KS_ARCH_X86, KS_MODE_64)
		self.libc = ctypes.CDLL("libc.so.6")

		self.reg_save, self.reg_save_addr = create_array(len(self.regs))
		self.stack, self.stack_addr = create_array(self.stack_size)
		# save orig rsp and rbp prior to running asm
		self.rsp_save, self.rsp_save_addr = create_ptr()
		self.rbp_save, self.rbp_save_addr = create_ptr()
		# save rsp across inputs
		self.rsp, self.rsp_addr = create_ptr(self.stack_addr + len(self.stack) * 8)
		self.flags, self.flags_addr = create_ptr()

		# 4. save all the regs in the buffer
		# 5. save flags to buffer
		# 6. mov the saved rsp and rbp to rsp and rbp
		self.epilogue = typing.cast(
			bytes,
			self.ks.asm(
				"; ".join(
					f"mov rax, {reg}; mov [{self.reg_save_addr + i * 8}], rax"
					for i, reg in enumerate(self.regs)
				)
				+ f";mov rax, rsp; mov [{self.rsp_addr}], rax; "
				+ f"mov rax, [{self.rsp_save_addr}]; mov rsp, rax; "
				+ f"mov rax, [{self.rbp_save_addr}]; mov rbp, rax; "
				f"pushfq; pop rax; mov [{self.flags_addr}], rax; ret; ",
				as_bytes=True,
			)[0],
		)

	def loop(self):
		self.history_file.touch(exist_ok=True)
		readline.read_history_file(self.history_file)
		while True:
			try:
				inp = input("iasm> ")
			except KeyboardInterrupt:
				print()
				continue
			except EOFError:
				break
			if inp.startswith("!"):
				self.run_python(inp[1:])
			elif inp.startswith("set "):
				self.set_display(inp.split(" ")[1:])
			elif inp.startswith(("reset ", "clear ")):
				self.clear_values(inp.split(" ")[1:])
			elif inp in {"help", "?"}:
				self.print_help()
			elif inp in {"exit", "quit"}:
				return
			else:
				self.run(inp)
			readline.write_history_file(self.history_file)

	def get_libc_address(self, func):
		return get_addr(self.libc[func])

	def run_python(self, code):
		try:
			print(
				eval(  # noqa: S307
					code,
					{
						"stack": list(self.stack),
						"flags": self.flags.contents.value,
						**self.regs,
					},
					{},
				)
			)
		except Exception:  # noqa: BLE001
			traceback.print_exc()

	def set_display(self, values):
		"""add/remove values from to_print"""
		if not values:
			print("No arg provided")
			return
		if "all" in values:
			values = ["stack", "flags", "regs"]
		for val in values:
			if val.startswith("-"):
				if val[1:] in self.to_print:
					self.to_print.remove(val[1:])
				else:
					print(f"{val} not in to_print")
			else:
				self.to_print.add(val)

	def clear_values(self, values):
		if not values:
			print("No arg provided")
			return
		if "all" in values:
			values = ["stack", "regs"]
		for val in values:
			if val == "stack":
				self.stack, self.stack_addr = create_array(self.stack_size)
			elif val == "regs":
				self.regs = {reg: 0 for reg in REG_NAMES}
			else:
				print(f"Invalid value {val}")

	def print_help(self):
		print(
			textwrap.dedent(
				"""\
		Help:
		You can provide any valid x64 assembly code to be run. For example, "mov rax, 1;".
		
		Other Commands:
		!<code> : evals python code with all registers, stack and flags as globals
		set [ stack | regs | flags_short | flags | all ] : set display of provided arg. 
		    Default is only regs. all sets stack, regs and flags.
		clear/reset [ stack | regs | all ] : clears value of provided arg
		help/? : prints this help page
		exit/quit/Ctrl-D : quits REPL"""
			)
		)

	def print_vals(self):
		if "stack" in self.to_print:
			print(list(self.stack))
		flags = self.flags.contents.value
		if "flags_short" in self.to_print:
			print(
				" ".join(
					short for i, (short, _) in FLAG_NAMES.items() if flags & (1 << i)
				)
			)
		if "flags" in self.to_print:
			print(
				" ".join(name for i, (_, name) in FLAG_NAMES.items() if flags & (1 << i))
			)
		if "regs" in self.to_print:
			print(self.regs)

	def assemble(self, asm: str) -> bytes:
		"""assemble into machine code"""
		# 1. clear flags
		# 2. set rsp and rbp to the stack location and save the original rsp and rbp
		# 3. mov all of the saved regs to the right spot
		code = typing.cast(
			bytes,
			self.ks.asm(
				"push 0; popfq;"
				"mov rbx, rsp; mov rcx, rbp;"
				f"mov rbp, {self.stack_addr + len(self.stack) * 8};"
				f"mov rsp, {self.rsp.contents.value};"
				f"mov rax, rbx; mov [{self.rsp_save_addr}], rax;"
				f"mov rax, rcx; mov [{self.rbp_save_addr}], rax; "
				+ "; ".join(f"mov {name}, {val}" for name, val in self.regs.items()),
				as_bytes=True,
			)[0],
		)
		# 4. run the user input
		# this is a separate call to ks.asm to reset rip to 0 for jumps
		user_code = typing.cast(bytes, self.ks.asm(asm, as_bytes=True)[0])
		if user_code is not None:
			code += user_code
		# 5. save all the regs in the buffer
		# 6. save flags to buffer
		# 7. mov the saved rsp and rbp to rsp and rbp
		code += self.epilogue
		return code

	def run(self, asm):
		"""run the assembly code"""
		# replaces <func> with libc address
		try:
			asm = re.sub(
				r"<(\w+)>", lambda m: str(self.get_libc_address(m.group(1))), asm
			)
		except IndexError as e:
			print(e)
			return

		try:
			code = self.assemble(asm)
		except KsError as e:
			print(e)
			return
		if "code" in self.to_print:
			print(code)

		run_shellcode(code)
		self.regs = dict(zip(REG_NAMES, self.reg_save))
		self.print_vals()


def main():
	import sys

	args = {"regs"}
	for arg in sys.argv[1:]:
		if arg.startswith("-") and arg[1:] in args:
			args.remove(arg[1:])
		else:
			args.add(arg)
	AsmRepl(args).loop()


if __name__ == "__main__":
	main()
