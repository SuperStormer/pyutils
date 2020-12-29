import ctypes
from enum import Flag

from .common import (Py_buffer, Py_hash_t, PyObject, PyObject_p, PyVarObject, Struct, update_types)

# https://github.com/python/cpython/blob/master/Include/cpython/bytesobject.h
class PyBytesObject(Struct):
	_fields_ = [("ob_base", PyVarObject), ("ob_shash", Py_hash_t), ("_ob_sval", ctypes.c_char * 1)]
	
	@property
	def ob_sval(self):
		return self.get_vla("_ob_sval", ctypes.c_char, self.ob_base.ob_size)
	
	value = ob_sval

# https://github.com/python/cpython/blob/master/Include/cpython/bytearrayobject.h
class PyByteArrayObject(Struct):
	_fields_ = [
		("ob_base", PyVarObject), ("ob_alloc", ctypes.c_ssize_t), ("ob_bytes", ctypes.c_char_p),
		("ob_start", ctypes.c_char_p), ("ob_exports", ctypes.c_ssize_t)
	]
	
	@property
	def value(self):
		return self.ob_start
	
	@value.setter
	def value(self, val):
		self.ob_start = val
		self.ob_base.ob_size = len(val)

# https://github.com/python/cpython/blob/master/Include/memoryobject.h
# and https://github.com/python/cpython/blob/master/Include/cpython/object.h

class PyManagedBufferObject(Struct):
	class Flags(Flag):
		RELEASED = 1
		FREE_FORMAT = 2
	
	_fields_ = [
		("ob_base", PyObject), ("flags", ctypes.c_int), ("exports", ctypes.c_ssize_t),
		("master", Py_buffer)
	]

class PyMemoryViewObject(Struct):
	class Flags(Flag):
		RELEASE = 1
		C = 2
		FORTRAN = 4
		SCALAR = 8
		PIL = 16
	
	_fields_ = [
		("ob_base", PyVarObject), ("mbuf", ctypes.POINTER(PyManagedBufferObject)),
		("hash", ctypes.c_ssize_t), ("flags", ctypes.c_int), ("exports", ctypes.c_ssize_t),
		("view", Py_buffer), ("weakreflist", PyObject_p), ("ob_array", (ctypes.c_ssize_t * 1))
	]
	
	def get_buffer(self, item_type=ctypes.c_char):
		return (item_type * (self.view.len // ctypes.sizeof(item_type))).from_address(self.view.buf)
	
	@property
	def buf(self):
		#separate method because properties don't take args
		return self.get_buffer()
	
	value = buf

update_types({bytearray: PyByteArrayObject, bytes: PyBytesObject, memoryview: PyMemoryViewObject})
