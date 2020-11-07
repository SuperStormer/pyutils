import ctypes
libc = ctypes.CDLL("libc.so.6")

def shellcode_to_func(shellcode: bytes, func_type=None):
	if func_type is None:
		func_type = ctypes.CFUNCTYPE(ctypes.c_int)
	buf = ctypes.c_void_p(libc.valloc(len(shellcode)))  # allocate page aligned
	libc.mprotect(buf, len(shellcode), 7)  # set to rwx
	ctypes.memmove(buf, shellcode, len(shellcode))
	return ctypes.cast(buf, func_type)

def run_shellcode(shellcode: bytes):
	return shellcode_to_func(shellcode)()
