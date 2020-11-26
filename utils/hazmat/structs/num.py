import ctypes
from .base import Struct
from .common import PyObject, PyVarObject, update_types

# https://github.com/python/cpython/blob/master/Include/longintrepr.h
class PyLongObject(Struct):
	SHIFT = 30
	BASE = 1 << SHIFT
	MASK = BASE - 1
	_fields_ = [("ob_base", PyVarObject), ("_ob_digit", ctypes.c_uint32)]
	
	@property
	def ob_digit(self):
		return self.get_vla("_ob_digit", ctypes.c_uint32, abs(self.ob_base.ob_size))
	
	@property
	def value(self):
		ob_size = self.ob_base.ob_size
		if ob_size == 0:
			return 0
		value = sum(val * 2**(PyLongObject.SHIFT * i) for i, val in enumerate(self.ob_digit))
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
class Py_complex(Struct):  #pylint: disable=invalid-name
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

update_types(
	{
	int: PyLongObject,
	float: PyFloatObject,
	complex: PyComplexObject,
	bool: PyLongObject,
	}
)
