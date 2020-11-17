#from ctypes import POINTER, c_char_p
import itertools
import ctypes
from enum import Enum, IntEnum
from typing import ValuesView

class Struct(ctypes.Structure):
	def __repr__(self):
		cls = type(self)
		delimiter = ",\n"
		return f"{cls.__name__}(\n{delimiter.join(f'{field[0]}={getattr(self,field[0])}' for field in cls._fields_ )})"
	
	def get_vla(self, field, typ, size):
		return (typ * size).from_address(ctypes.addressof(self) + getattr(type(self), field).offset)

class Union(ctypes.Union):
	def __repr__(self):
		cls = type(self)
		delimiter = ",\n"
		return f"{cls.__name__}(\n{delimiter.join(f'{field[0]}={getattr(self,field[0])}' for field in cls._fields_ )})"

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

class PyVarObject(Struct):
	_fields_ = [("ob_base", PyObject), ("ob_size", ctypes.c_ssize_t)]

Py_hash_t = ctypes.c_ssize_t

# https://github.com/python/cpython/blob/master/Include/longintrepr.h
class PyLongObject(Struct):
	SHIFT = 30
	_fields_ = [("ob_base", PyVarObject), ("_ob_digit", ctypes.c_uint32)]
	
	@property
	def ob_digit(self):
		ob_size = self.ob_base.ob_size
		if ob_size == 0:
			return 0
		value = sum(
			val * 2**(PyLongObject.SHIFT * i)
			for i, val in enumerate(self.get_vla("_ob_digit", ctypes.c_uint32, abs(ob_size)))
		)
		sign = 1 if ob_size > 0 else -1
		return sign * value
	
	value = ob_digit

# https://github.com/python/cpython/blob/master/Include/floatobject.h
class PyFloatObject(Struct):
	_fields_ = [("ob_base", PyObject), ("ob_fval", ctypes.c_double)]
	
	@property
	def value(self):
		return self.ob_fval

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

class PyAsciiObject(Struct):
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
	
	def to_compact_unicode(self):
		return PyCompactUnicodeObject.from_address(ctypes.addressof(self))
	
	def to_unicode(self):
		return PyUnicodeObject.from_address(ctypes.addressof(self))
	
	def get_real(self):
		"""get the real str class """
		if self.state.compact:
			if self.state.ascii:
				return self
			else:
				return self.to_compact_unicode()
		else:
			return self.to_unicode()

class PyCompactUnicodeObject(Struct):
	_fields_ = [
		("_base", PyAsciiObject), ("utf8_length", ctypes.c_ssize_t), ("utf8", ctypes.c_char_p),
		("wstr_length", ctypes.c_ssize_t)
	]
	
	@property
	def value(self):
		""" gets str value (data is stored after the struct for some reason)"""
		char_type = self._base.char_type().type
		return (char_type * self._base.length
				).from_address(ctypes.addressof(self) + ctypes.sizeof(PyCompactUnicodeObject))
	
	def to_unicode(self):
		return PyUnicodeObject(ctypes.addressof(self))

class PyUnicodeObject(Struct):
	class Data(Union):
		#pylint: disable=no-member
		_fields_ = [
			("any", ctypes.c_void_p), ("latin1", ctypes.POINTER(CharType.Py_UCS1.type)), #type:ignore 
			("ucs2", ctypes.POINTER(CharType.Py_UCS2.type)), #type:ignore 
			("ucs4", ctypes.POINTER(CharType.Py_UCS4.type)) #type:ignore 
		]
	
	@property
	def value(self):
		ascii_obj = self._base._base  #pylint: disable=protected-access
		char_type = ascii_obj.char_type().type
		arr_type = char_type * ascii_obj.length
		field_addr = self.data.any.value
		return arr_type.from_address(field_addr)

PyUnicodeObject._fields_ = [("_base", PyCompactUnicodeObject), ("data", PyUnicodeObject.Data)]

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
