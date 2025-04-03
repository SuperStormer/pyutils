import ctypes


def get_addr(ptr: ctypes._Pointer):
	"""returns address pointer is pointing at"""
	return ctypes.cast(ptr, ctypes.c_void_p).value
