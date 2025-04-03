import ctypes
import sys
from enum import Enum

from .base import Struct, field
from .common import (
	Py_GIL_DISABLED,
	Py_hash_t,
	PyMutex,
	PyObject,
	PyObject_p,
	update_types,
)


# https://github.com/python/cpython/blob/master/Include/cpython/dictobject.h
# and https://github.com/python/cpython/blob/main/Include/internal/pycore_dict.h
class PyDictObject(Struct):
	@property
	def indices(self):
		return self.ma_keys[0].dk_indices

	@property
	def items(self):
		if ctypes.cast(self.ma_values, ctypes.c_void_p).value is None:
			return self.ma_keys[0].dk_entries
		else:  # TODO
			raise NotImplementedError(
				"split table not implemented, see "
				"https://github.com/python/cpython/blob/master/Include/cpython/dictobject.h"
			)

	value = items


class PyDictKeyEntry(Struct):
	me_hash = field(Py_hash_t)
	me_key = field(PyObject_p)
	me_value = field(PyObject_p)


if sys.version_info >= (3, 11):

	class PyDictUnicodeEntry(Struct):
		me_key = field(PyObject_p)
		me_value = field(PyObject_p)

	class DictKeysKind(Enum):
		DICT_KEYS_GENERAL = 0
		DICT_KEYS_UNICODE = 1
		DICT_KEYS_SPLIT = 2

	class PyDictKeysObject(Struct):
		DKIX_EMPTY = -1
		DKIX_DUMMY = -2
		DKIX_ERROR = -3
		_fields_ = (
			[
				("dk_refcnt", ctypes.c_ssize_t),
				("dk_log2_size", ctypes.c_uint8),
				("dk_log2_index_bytes", ctypes.c_uint8),
				("_dk_kind", ctypes.c_uint8),
			]
			+ ([("dk_mutex", PyMutex)] if Py_GIL_DISABLED else [])
			+ [
				("dk_version", ctypes.c_uint32),
				("dk_usable", ctypes.c_ssize_t),
				("dk_nentries", ctypes.c_ssize_t),
				("_dk_indices", ctypes.c_byte * 1),
			]
		)

		@property
		def dk_kind(self):
			return DictKeysKind(self._dk_kind)

		@property
		def indices_type(self):
			if self.dk_log2_size <= 8:
				return ctypes.c_byte
			elif self.dk_log2_size <= 16:
				return ctypes.c_int16
			elif self.dk_log2_size <= 32:
				return ctypes.c_int32
			else:
				return ctypes.c_int64

		@property
		def entry_type(self):
			if self.dk_kind == DictKeysKind.DICT_KEYS_UNICODE:
				return PyDictUnicodeEntry
			else:
				return PyDictKeyEntry

		@property
		def dk_indices(self):
			typ = self.indices_type
			return self.get_vla(
				"_dk_indices", typ, (1 << self.dk_log2_index_bytes) * ctypes.sizeof(typ)
			)

		@property
		def dk_entries(self):
			return (self.entry_type * self.dk_nentries).from_address(
				ctypes.addressof(self)
				+ type(self)._dk_indices.offset  # noqa: SLF001
				+ (1 << self.dk_log2_index_bytes) * ctypes.sizeof(self.indices_type)
			)

else:
	dict_lookup_func = ctypes.PYFUNCTYPE(
		ctypes.c_ssize_t,
		ctypes.POINTER(PyDictObject),
		PyObject_p,
		Py_hash_t,
		ctypes.POINTER(PyObject_p),
	)

	class PyDictKeysObject(Struct):
		DKIX_EMPTY = -1
		DKIX_DUMMY = -2
		DKIX_ERROR = -3
		dk_refcnt = field(ctypes.c_ssize_t)
		dk_size = field(ctypes.c_ssize_t)
		dk_lookup = field(dict_lookup_func)
		dk_usable = field(ctypes.c_ssize_t)
		dk_nentries = field(ctypes.c_ssize_t)
		_dk_indices = field(ctypes.c_byte * 1)

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
				ctypes.addressof(self)
				+ type(self)._dk_indices.offset  # noqa: SLF001
				+ self.dk_size * ctypes.sizeof(self.indices_type)
			)


class PyDictViewObject(Struct):
	ob_base = field(PyObject)
	dv_dict = field(ctypes.POINTER(PyDictObject))


# these aren't real structs, they're implemented w/ PyDictViewObject with a different ob_type
class PyDictValues(PyDictViewObject):
	pass


class PyDictKeys(PyDictViewObject):
	pass


if sys.version_info >= (3, 14):
	PyDictObject._fields_ = [
		("ob_base", PyObject),
		("ma_used", ctypes.c_ssize_t),
		("ma_watcher_tag", ctypes.c_uint64),
		("ma_keys", ctypes.POINTER(PyDictKeysObject)),
		("ma_values", ctypes.POINTER(PyObject_p)),
	]
else:
	PyDictObject._fields_ = [
		("ob_base", PyObject),
		("ma_used", ctypes.c_ssize_t),
		("ma_version_tag", ctypes.c_uint64),
		("ma_keys", ctypes.POINTER(PyDictKeysObject)),
		("ma_values", ctypes.POINTER(PyObject_p)),
	]

update_types({
	dict: PyDictObject,
	type({}.keys()): PyDictKeys,
	type({}.values()): PyDictValues,
})
