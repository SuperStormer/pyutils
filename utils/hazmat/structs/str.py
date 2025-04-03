import ctypes
import sys
from enum import Enum

from .base import Struct, Union
from .common import Py_hash_t, PyObject, update_types


# https://github.com/python/cpython/blob/master/Include/cpython/unicodeobject.h
class CharType(Enum):
	type: type[ctypes._SimpleCData]
	kind: str
	if sys.version_info < (3, 11):
		wchar_t = (0, ctypes.c_wchar, "PyUnicode_WCHAR_KIND")
	Py_UCS1 = (1, ctypes.c_uint8, "PyUnicode_1BYTE_KIND")
	Py_UCS2 = (2, ctypes.c_uint16, "PyUnicode_2BYTE_KIND")
	Py_UCS4 = (4, ctypes.c_uint32, "PyUnicode_4BYTE_KIND")

	def __new__(cls, value, typ, kind):
		self = object.__new__(cls)
		self._value_ = value
		self.type = typ
		self.kind = kind
		return self


class PyStrMixin:
	def to_ascii(self):
		return PyAsciiObject.from_address(ctypes.addressof(self))  # pyright: ignore reportArgumentType

	def to_compact_unicode(self):
		return PyCompactUnicodeObject.from_address(ctypes.addressof(self))  # pyright: ignore reportArgumentType

	def to_unicode(self):
		return PyUnicodeObject.from_address(ctypes.addressof(self))  # pyright: ignore reportArgumentType


class PyAsciiObject(Struct, PyStrMixin):
	class InternState(Enum):
		SSTATE_NOT_INTERNED = 0
		SSTATE_INTERNED_MORTAL = 1
		SSTATE_INTERNED_IMMORTAL = 2

	class State(Struct):
		if sys.version_info >= (3, 14):
			_fields_ = [
				("interned", ctypes.c_uint16),
				("kind", ctypes.c_ushort, 3),
				("compact", ctypes.c_ushort, 1),
				("ascii", ctypes.c_ushort, 1),
				("statically_allocated", ctypes.c_ushort, 1),
				("_padding", ctypes.c_ushort, 10),
			]
		elif sys.version_info >= (3, 12):
			_fields_ = [
				("interned", ctypes.c_uint, 2),
				("kind", ctypes.c_uint, 3),
				("compact", ctypes.c_uint, 1),
				("ascii", ctypes.c_uint, 1),
				("_padding", ctypes.c_uint, 25),
			]
		else:
			_fields_ = [
				("interned", ctypes.c_uint, 2),
				("kind", ctypes.c_uint, 3),
				("compact", ctypes.c_uint, 1),
				("ascii", ctypes.c_uint, 1),
				("ready", ctypes.c_uint, 1),
				("_padding", ctypes.c_uint, 24),
			]

	if sys.version_info >= (3, 12):
		_fields_ = [
			("ob_base", PyObject),
			("length", ctypes.c_ssize_t),
			("hash", Py_hash_t),
			("state", State),
		]
	else:
		_fields_ = [
			("ob_base", PyObject),
			("length", ctypes.c_ssize_t),
			("hash", Py_hash_t),
			("state", State),
			("wstr", ctypes.c_wchar_p),
		]

	@property
	def value(self):
		"""gets str value (data is stored after the struct for some reason)"""
		end_addr = ctypes.addressof(self) + ctypes.sizeof(PyAsciiObject)
		return (ctypes.c_char * self.length).from_address(end_addr)

	@property
	def intern_state(self):
		return PyAsciiObject.InternState(self.state.interned)

	@property
	def char_type(self):
		return CharType(self.state.kind)

	def get_real(self):
		"""get the real str class"""
		if self.state.compact:
			if self.state.ascii:
				return self
			else:
				return self.to_compact_unicode()
		else:
			return self.to_unicode()


class PyCompactUnicodeObject(Struct, PyStrMixin):
	if sys.version_info >= (3, 12):
		_fields_ = [
			("_base", PyAsciiObject),
			("utf8_length", ctypes.c_ssize_t),
			("utf8", ctypes.c_char_p),
		]
	else:
		_fields_ = [
			("_base", PyAsciiObject),
			("utf8_length", ctypes.c_ssize_t),
			("utf8", ctypes.c_char_p),
			("wstr_length", ctypes.c_ssize_t),
		]

	@property
	def value(self):
		"""gets str value (data is stored after the struct for some reason)"""
		char_type = self._base.char_type.type
		end_addr = ctypes.addressof(self) + ctypes.sizeof(PyCompactUnicodeObject)
		return (char_type * self._base.length).from_address(end_addr)


class PyUnicodeObject(Struct, PyStrMixin):
	class Data(Union):
		_fields_ = [
			("any", ctypes.c_void_p),
			("latin1", ctypes.POINTER(CharType.Py_UCS1.type)),
			("ucs2", ctypes.POINTER(CharType.Py_UCS2.type)),
			("ucs4", ctypes.POINTER(CharType.Py_UCS4.type)),
		]

	_fields_ = [("_base", PyCompactUnicodeObject), ("data", Data)]

	@property
	def value(self):
		ascii_obj = self._base._base  # noqa: SLF001
		char_type = ascii_obj.char_type
		if sys.version_info < (3, 11) and char_type == CharType.wchar_t:
			return ascii_obj.wstr
		else:
			arr_type = char_type.type * ascii_obj.length
			field_addr = self.data.any
			return arr_type.from_address(field_addr)


update_types({str: PyAsciiObject})
