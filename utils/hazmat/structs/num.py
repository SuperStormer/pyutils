import ctypes
import sys
import warnings

from .base import Struct, field
from .common import PyObject, PyVarObject, update_types

# https://github.com/python/cpython/blob/master/Include/cpython/longintrepr.h
# credit to Crowthebird#1649 (<@!675937585624776717>) for digit size check
if sys.version_info >= (3, 12):
	# TODO _digit_size check for 3.12+
	_digit_size = 0
else:
	_digit_size = PyVarObject.from_object(32768).ob_size - 1
_digit_type = (ctypes.c_uint32, ctypes.c_ushort)[_digit_size]

PyLong_NON_SIZE_BITS = 3
PyLong_SHIFT = (30, 15)[_digit_size]
PyLong_BASE = 1 << PyLong_SHIFT
PyLong_MASK = PyLong_BASE - 1

if sys.version_info >= (3, 12):

	class PyLongValue(Struct):
		lv_tag = field(ctypes.c_ulong)
		_ob_digit = field(_digit_type)

		@property
		def ob_digit(self):
			return self.get_vla("_ob_digit", _digit_type, self.ndigits)

		@property
		def ndigits(self):
			return self.lv_tag >> PyLong_NON_SIZE_BITS

		@property
		def value(self):
			# 2 lower bits
			# 0 is positive, 1 is zero, 2 is negative
			sign_bits = self.lv_tag & ~3
			if sign_bits == 1:
				return 0
			value = sum(
				val * 2 ** (PyLong_SHIFT * i) for i, val in enumerate(self.ob_digit)
			)
			sign = 1 if sign_bits == 0 else -1
			return sign * value

		@value.setter
		def value(self, val: int):
			val = abs(val)
			digits = []
			while val > 0:
				digits.append(val & PyLong_MASK)
				val >>= PyLong_SHIFT
			if len(digits) > abs(self.ndigits):
				warnings.warn(
					f"Number of digits ({len(digits)}) is greater than current ({self.ndigits})",
					stacklevel=3,
				)
			sign_bits = 0 if val > 0 else 1 if val == 0 else 2
			self.lv_tag = (len(digits) << PyLong_NON_SIZE_BITS) | sign_bits
			ctypes.memmove(
				self.ob_digit, (_digit_type * len(digits))(*digits), len(digits)
			)

		def is_small_int(self):
			return bool(self.lv_tag & (1 << 3))

	class PyLongObject(Struct):
		ob_base = field(PyObject)
		long_value = field(PyLongValue)

		@property
		def value(self):
			return self.long_value.value

		@value.setter
		def value(self, val: int):
			self.long_value.value = val

else:

	class PyLongObject(Struct):
		ob_base = field(PyVarObject)
		_ob_digit = field(_digit_type)

		@property
		def ob_digit(self):
			return self.get_vla("_ob_digit", _digit_type, self.ndigits)

		@property
		def ndigits(self):
			return abs(self.ob_base.ob_size)

		@property
		def value(self):
			ob_size = self.ob_base.ob_size
			if ob_size == 0:
				return 0
			value = sum(
				val * 2 ** (PyLong_SHIFT * i) for i, val in enumerate(self.ob_digit)
			)
			sign = 1 if ob_size > 0 else -1
			return sign * value

		@value.setter
		def value(self, val: int):
			sign = 1 if val > 0 else -1
			val = abs(val)
			digits = []
			while val > 0:
				digits.append(val & PyLong_MASK)
				val >>= PyLong_SHIFT
			if len(digits) > self.ndigits:
				warnings.warn(
					f"Number of digits ({len(digits)}) is greater than current ({self.ndigits})",
					stacklevel=3,
				)
			self.ob_base.ob_size = len(digits) * sign
			ctypes.memmove(
				self.ob_digit, (_digit_type * len(digits))(*digits), len(digits)
			)


Py_True = PyLongObject.from_address(id(True))  # noqa: FBT003
Py_False = PyLongObject.from_address(id(False))  # noqa: FBT003


# https://github.com/python/cpython/blob/master/Include/floatobject.h
class PyFloatObject(Struct):
	ob_base = field(PyObject)
	ob_fval = field(ctypes.c_double)

	@property
	def value(self):
		return self.ob_fval

	@value.setter
	def value(self, val):
		self.ob_fval = val


# https://github.com/python/cpython/blob/master/Include/complexobject.h
class Py_complex(Struct):  # noqa: N801
	real = field(ctypes.c_double)
	imag = field(ctypes.c_double)


class PyComplexObject(Struct):
	ob_base = field(PyObject)
	cval = field(Py_complex)

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
		self.cval.imag = val

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
