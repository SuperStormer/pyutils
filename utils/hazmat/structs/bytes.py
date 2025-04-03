import ctypes
import warnings
from enum import Flag

from .base import Struct, field
from .common import (
	Py_buffer,
	Py_hash_t,
	PyObject,
	PyObject_p,
	PyVarObject,
	update_types,
)


# https://github.com/python/cpython/blob/master/Include/cpython/bytesobject.h
class PyBytesObject(Struct):
	ob_base = field(PyVarObject)
	ob_shash = field(Py_hash_t)
	_ob_sval = field(ctypes.c_char * 1)

	@property
	def ob_sval(self):
		return self.get_vla("_ob_sval", ctypes.c_char, self.ob_base.ob_size)

	@ob_sval.setter
	def ob_sval(self, val):
		self.ob_sval.value = val

	@property
	def value(self):
		return self.ob_sval

	@value.setter
	def value(self, val):
		if len(val) > self.ob_base.ob_size:
			warnings.warn(
				f"Length ({len(val)}) is greater than current ({self.ob_base.ob_size})",
				stacklevel=3,
			)
		self.ob_base.ob_size = len(val)
		self.ob_sval = val


# https://github.com/python/cpython/blob/master/Include/cpython/bytearrayobject.h
class PyByteArrayObject(Struct):
	ob_base = field(PyVarObject)
	ob_alloc = field(ctypes.c_ssize_t)
	ob_bytes = field(ctypes.c_char_p)
	ob_start = field(ctypes.c_char_p)
	ob_exports = field(ctypes.c_ssize_t)

	@property
	def value(self):
		return self.ob_start

	@value.setter
	def value(self, val):
		if len(val) > self.ob_base.ob_size:
			warnings.warn(
				f"Length ({len(val)}) is greater than current ({self.ob_base.ob_size})",
				stacklevel=3,
			)
		self.ob_base.ob_size = len(val)
		self.ob_start = val


# https://github.com/python/cpython/blob/master/Include/memoryobject.h
# and https://github.com/python/cpython/blob/master/Include/cpython/object.h


class PyManagedBufferObject(Struct):
	class Flags(Flag):
		RELEASED = 1
		FREE_FORMAT = 2

	ob_base = field(PyObject)
	flags = field(ctypes.c_int)
	exports = field(ctypes.c_ssize_t)
	master = field(Py_buffer)


class PyMemoryViewObject(Struct):
	class Flags(Flag):
		RELEASE = 1
		C = 2  # pylint: disable=invalid-name
		FORTRAN = 4
		SCALAR = 8
		PIL = 16

	ob_base = field(PyVarObject)
	mbuf = field(ctypes.POINTER(PyManagedBufferObject))
	hash = field(Py_hash_t)
	flags = field(ctypes.c_int)
	exports = field(ctypes.c_ssize_t)
	view = field(Py_buffer)
	weakreflist = field(PyObject_p)
	ob_array = field(ctypes.c_ssize_t * 1)

	def get_buffer(self, item_type=ctypes.c_char):
		return (item_type * (self.view.len // ctypes.sizeof(item_type))).from_address(
			self.view.buf
		)

	@property
	def buf(self):
		# separate method because properties don't take args
		return self.get_buffer()

	value = buf


update_types({
	bytearray: PyByteArrayObject,
	bytes: PyBytesObject,
	memoryview: PyMemoryViewObject,
})
