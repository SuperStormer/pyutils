import ctypes

from .base import Struct
from .common import PyObject, PyObject_p, Py_hash_t

# https://github.com/python/cpython/blob/master/Include/cpython/dictobject.h
# and https://github.com/python/cpython/blob/master/Objects/dict-common.h
class PyDictObject(Struct):
	@property
	def indices(self):
		return self.ma_keys[0].dk_indices
	
	@property
	def items(self):
		if ctypes.cast(self.ma_values, ctypes.c_void_p).value is None:
			return self.ma_keys[0].dk_entries
		else:  #TODO
			raise NotImplementedError(
				"split table not implemented, see "
				"https://github.com/python/cpython/blob/master/Include/cpython/dictobject.h"
			)
	
	value = items

class PyDictKeyEntry(Struct):
	_fields_ = [("me_hash", Py_hash_t), ("me_key", PyObject_p), ("me_value", PyObject_p)]

dict_lookup_func = ctypes.CFUNCTYPE(
	ctypes.c_ssize_t, ctypes.POINTER(PyDictObject), PyObject_p, Py_hash_t,
	ctypes.POINTER(PyObject_p)
)

class PyDictKeysObject(Struct):
	DKIX_EMPTY = -1
	DKIX_DUMMY = -2
	DKIX_ERROR = -3
	_fields_ = [
		("dk_refcnt", ctypes.c_ssize_t), ("dk_size", ctypes.c_ssize_t),
		("dk_lookup", dict_lookup_func), ("dk_usable", ctypes.c_ssize_t),
		("dk_nentries", ctypes.c_ssize_t), ("_dk_indices", ctypes.c_byte * 1)
	]
	
	@property
	def indices_type(self):
		if self.dk_size <= (1 << 8):
			return ctypes.c_byte
		elif self.dk_size <= (1 << 16):
			return ctypes.c_int16
		elif self.dk_size <= (1 << 32):
			return ctypes.c_int32
		else:
			return ctypes.c_int64
	
	@property
	def dk_indices(self):
		typ = self.indices_type
		return self.get_vla("_dk_indices", typ, self.dk_size * ctypes.sizeof(typ))
	
	@property
	def dk_entries(self):
		return (PyDictKeyEntry * self.dk_nentries).from_address(
			ctypes.addressof(self) + type(self)._dk_indices.offset +
			self.dk_size * ctypes.sizeof(self.indices_type)
		)

PyDictObject._fields_ = [ #pylint: disable=protected-access
	("ob_base", PyObject), ("ma_used", ctypes.c_ssize_t), ("ma_version_tag", ctypes.c_uint64),
	("ma_keys", ctypes.POINTER(PyDictKeysObject)), ("ma_values", ctypes.POINTER(PyObject_p))
]
