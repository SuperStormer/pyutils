import ctypes
import warnings

from .base import Struct
from .common import PyObject, PyVarObject, update_types

# https://github.com/python/cpython/blob/master/Include/cpython/longintrepr.h
# credit to Crowthebird#1649 (<@!675937585624776717>) for digit size check
_digit_size = PyVarObject.from_object(32768).ob_size - 1
_digit_type = (ctypes.c_uint32, ctypes.c_ushort)[_digit_size]


class PyLongObject(Struct):
	SHIFT = (30, 15)[_digit_size]
	BASE = 1 << SHIFT
	MASK = BASE - 1
	_fields_ = [("ob_base", PyVarObject), ("_ob_digit", _digit_type)]

	@property
	def ob_digit(self):
		return self.get_vla("_ob_digit", _digit_type, abs(self.ob_base.ob_size))

	@property
	def value(self):
		ob_size = self.ob_base.ob_size
		if ob_size == 0:
			return 0
		value = sum(
			val * 2 ** (PyLongObject.SHIFT * i) for i, val in enumerate(self.ob_digit)
		)
		sign = 1 if ob_size > 0 else -1
		return sign * value

	@value.setter
	def value(self, val):
		sign = 1 if val > 0 else -1
		val = abs(val)
		digits = []
		while val > 0:
			digits.append(val & PyLongObject.MASK)
			val >>= PyLongObject.SHIFT
		if len(digits) > abs(self.ob_base.ob_size):
			warnings.warn(
				f"Number of digits ({len(digits)}) is greater than current ({self.ob_base.ob_size})",
				stacklevel=2,
			)
		self.ob_base.ob_size = len(digits) * sign
		ctypes.memmove(self.ob_digit, (_digit_type * len(digits))(*(digits)), len(digits))


Py_True = PyLongObject.from_address(id(True))
Py_False = PyLongObject.from_address(id(False))


# https://github.com/python/cpython/blob/master/Include/floatobject.h
class PyFloatObject(Struct):
	_fields_ = [("ob_base", PyObject), ("ob_fval", ctypes.c_double)]

	@property
	def value(self):
		return self.ob_fval

	@value.setter
	def value(self, val):
		self.ob_fval = val


# https://github.com/python/cpython/blob/master/Include/complexobject.h
class Py_complex(Struct):  # noqa: N801
	_fields_ = [("real", ctypes.c_double), ("imag", ctypes.c_double)]


class PyComplexObject(Struct):
	_fields_ = [("ob_base", PyObject), ("cval", Py_complex)]

	@property
	def real(self):
		return self.cval.real

	@real.setter
	def real(self, val):
		self.cval.real = val

	@property
	def imag(self):
		return self.cval.imag

	@imag.setter
	def imag(self, val):
		self.cval.real.imag = val

	@property
	def value(self):
		return complex(self.real, self.imag)

	@value.setter
	def value(self, val: complex):
		self.cval.real = val.real
		self.cval.imag = val.imag


update_types({
	int: PyLongObject,
	float: PyFloatObject,
	complex: PyComplexObject,
	bool: PyLongObject,
})
