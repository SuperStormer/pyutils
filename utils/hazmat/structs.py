import itertools
import ctypes
from enum import Enum

class Struct(ctypes.Structure):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(f'{field[0]}={getattr(self, field[0])}' for field in cls._fields_)
		return f"{cls.__name__}(\n{fields})"
	
	def get_vla(self, field, typ, size):
		return (typ * size).from_address(ctypes.addressof(self) + getattr(type(self), field).offset)

class Union(ctypes.Union):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(f'{field[0]}={getattr(self, field[0])}' for field in cls._fields_)
		return f"{cls.__name__}(\n{fields})"

# https://github.com/python/cpython/blob/master/Include/object.h
#define PyObject_HEAD          PyObject ob_base;
#define PyObject_VAR_HEAD      PyVarObject ob_base;
types = [
	bool, memoryview, bytearray, bytes, classmethod, complex, dict, enumerate, filter, float,
	frozenset, property, int, list, map, object, range, reversed, set, slice, staticmethod, str,
	super, tuple, type, zip
]
type_dict = {id(t): t for t in types}

PyTypeObject_p = ctypes.c_void_p  #TODO

class PyObject(Struct):
	_fields_ = [("ob_refcnt", ctypes.c_ssize_t), ("ob_type", PyTypeObject_p)]
	
	def get_type(self):
		return type_dict[self.ob_type]

PyObject_p = ctypes.POINTER(PyObject)
Py_None = PyObject.from_address(id(None))
Py_Ellipsis = PyObject.from_address(id(Ellipsis))

class PyVarObject(Struct):
	_fields_ = [("ob_base", PyObject), ("ob_size", ctypes.c_ssize_t)]

Py_hash_t = ctypes.c_ssize_t

# https://github.com/python/cpython/blob/master/Include/longintrepr.h
class PyLongObject(Struct):
	SHIFT = 30
	_fields_ = [("ob_base", PyVarObject), ("_ob_digit", ctypes.c_uint32)]
	
	@property
	def ob_digit(self):
		return self.get_vla("_ob_digit", ctypes.c_uint32, abs(self.ob_base.ob_size))
	
	@property
	def value(self):
		ob_size = self.ob_base.ob_size
		if ob_size == 0:
			return 0
		value = sum(val * 2**(PyLongObject.SHIFT * i) for i, val in enumerate(self.ob_digit()))
		sign = 1 if ob_size > 0 else -1
		return sign * value

Py_True = PyLongObject.from_address(id(True))
Py_False = PyLongObject.from_address(id(False))

# https://github.com/python/cpython/blob/master/Include/floatobject.h
class PyFloatObject(Struct):
	_fields_ = [("ob_base", PyObject), ("ob_fval", ctypes.c_double)]
	
	@property
	def value(self):
		return self.ob_fval

# https://github.com/python/cpython/blob/master/Include/complexobject.h
class Py_complex(Struct):
	_fields_ = [("real", ctypes.c_double), ("imag", ctypes.c_double)]

class PyComplexObject(Struct):
	_fields_ = [("ob_base", PyObject), ("cval", Py_complex)]
	
	@property
	def real(self):
		return self.cval.real
	
	@property
	def imag(self):
		return self.cval.imag
	
	@property
	def value(self):
		return complex(self.real, self.imag)

# https://github.com/python/cpython/blob/master/Include/cpython/tupleobject.h
class PyTupleObject(Struct):
	_fields_ = [("ob_base", PyVarObject), ("_ob_item", PyObject_p)]
	
	@property
	def ob_item(self):
		return self.get_vla("_ob_item", PyObject_p, self.ob_base.ob_size)
	
	value = ob_item

# https://github.com/python/cpython/blob/master/Include/cpython/bytesobject.h
class PyBytesObject(Struct):
	_fields_ = [("ob_base", PyVarObject), ("ob_shash", Py_hash_t), ("_ob_sval", ctypes.c_char)]
	
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

# https://github.com/python/cpython/blob/master/Include/cpython/unicodeobject.h
class CharType(Enum):
	wchar_t = (0, ctypes.c_wchar, "PyUnicode_WCHAR_KIND")
	Py_UCS1 = (1, ctypes.c_uint8, "PyUnicode_1BYTE_KIND")
	Py_UCS2 = (2, ctypes.c_uint16, "PyUnicode_2BYTE_KIND")
	Py_UCS4 = (4, ctypes.c_uint32, "PyUnicode_4BYTE_KIND")
	
	def __new__(cls, value, type, kind):
		self = object.__new__(cls)
		self._value_ = value
		self.type = type
		self.kind = kind
		return self

class PyStrMixin():
	def to_ascii(self):
		return PyAsciiObject.from_address(ctypes.addressof(self))
	
	def to_compact_unicode(self):
		return PyCompactUnicodeObject.from_address(ctypes.addressof(self))
	
	def to_unicode(self):
		return PyUnicodeObject.from_address(ctypes.addressof(self))

class PyAsciiObject(Struct, PyStrMixin):
	class InternState(Enum):
		SSTATE_NOT_INTERNED = 0
		SSTATE_INTERNED_MORTAL = 1
		SSTATE_INTERNED_IMMORTAL = 2
	
	class State(Struct):
		_fields_ = [
			("interned", ctypes.c_uint, 2), ("kind", ctypes.c_uint, 3),
			("compact", ctypes.c_uint, 1), ("ascii", ctypes.c_uint, 1), ("ready", ctypes.c_uint, 1),
			("_padding", ctypes.c_uint, 24)
		]
	
	_fields_ = [
		("ob_base", PyObject), ("length", ctypes.c_ssize_t), ("hash", Py_hash_t), ("state", State),
		("wstr", ctypes.c_wchar_p)
	]
	
	@property
	def value(self):
		""" gets str value (data is stored after the struct for some reason)"""
		return (ctypes.c_char *
			self.length).from_address(ctypes.addressof(self) + ctypes.sizeof(PyAsciiObject))
	
	@property
	def intern_state(self):
		return PyAsciiObject.InternState(self.state.interned)
	
	@property
	def char_type(self):
		return CharType(self.state.kind)  #type:ignore #pylint: disable=no-value-for-parameter
	
	def get_real(self):
		"""get the real str class """
		if self.state.compact:
			if self.state.ascii:
				return self
			else:
				return self.to_compact_unicode()
		else:
			return self.to_unicode()

class PyCompactUnicodeObject(Struct, PyStrMixin):
	_fields_ = [
		("_base", PyAsciiObject), ("utf8_length", ctypes.c_ssize_t), ("utf8", ctypes.c_char_p),
		("wstr_length", ctypes.c_ssize_t)
	]
	
	@property
	def value(self):
		""" gets str value (data is stored after the struct for some reason)"""
		char_type = self._base.char_type.type
		return (char_type * self._base.length
				).from_address(ctypes.addressof(self) + ctypes.sizeof(PyCompactUnicodeObject))

class PyUnicodeObject(Struct, PyStrMixin):
	class Data(Union):
		#pylint: disable=no-member
		_fields_ = [
			("any", ctypes.c_void_p),
			("latin1", ctypes.POINTER(CharType.Py_UCS1.type)),  #type:ignore 
			("ucs2", ctypes.POINTER(CharType.Py_UCS2.type)),  #type:ignore 
			("ucs4", ctypes.POINTER(CharType.Py_UCS4.type))  #type:ignore 
		]
	
	_fields_ = [("_base", PyCompactUnicodeObject), ("data", Data)]
	
	@property
	def value(self):
		ascii_obj = self._base._base  #pylint: disable=protected-access
		char_type = ascii_obj.char_type
		if char_type == CharType.wchar_t:
			return ascii_obj.wstr
		else:
			arr_type = char_type.type * ascii_obj.length
			field_addr = self.data.any
			return arr_type.from_address(field_addr)

# https://github.com/python/cpython/blob/master/Include/cpython/listobject.h
class PyListObject(Struct):
	_fields_ = [
		("ob_base", PyVarObject), ("_ob_item", ctypes.POINTER(PyObject_p)),
		("allocated", ctypes.c_ssize_t)
	]
	
	@property
	def ob_item(self):
		return list(itertools.islice(self._ob_item, 0, self.ob_base.ob_size))
	
	value = ob_item

# https://github.com/python/cpython/blob/master/Include/setobject.h
class setentry(Struct):
	_fields_ = [("key", PyObject_p), ("hash", Py_hash_t)]

PySet_MINSIZE = 8

class PySetObject(Struct):
	_fields_ = [
		("ob_base", PyObject), ("fill", ctypes.c_ssize_t), ("used", ctypes.c_ssize_t),
		("mask", ctypes.c_ssize_t), ("_table", ctypes.POINTER(setentry)), ("hash", Py_hash_t),
		("finger", ctypes.c_ssize_t), ("smalltable", (setentry * PySet_MINSIZE)),
		("weakreflist", PyObject_p)
	]
	
	@property
	def table(self):
		return itertools.islice(self._table, self.mask + 1)
	
	value = table

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
				"split table not implemented, see https://github.com/python/cpython/blob/master/Include/cpython/dictobject.h"
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
		("dk_nentries", ctypes.c_ssize_t), ("_dk_indices", ctypes.c_byte)
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

PyDictObject._fields_ = [
	("ob_base", PyObject), ("ma_used", ctypes.c_ssize_t), ("ma_version_tag", ctypes.c_uint64),
	("ma_keys", ctypes.POINTER(PyDictKeysObject)), ("ma_values", ctypes.POINTER(PyObject_p))
]
