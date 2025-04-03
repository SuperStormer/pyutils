import ctypes

from .base import Struct, field
from .common import (
	PyMethodDef,
	PyObject_p,
	PyTypeObject_p,
	vectorcallfunc,
)


# https://github.com/python/cpython/blob/main/Include/cpython/methodobject.h
class PyCFunctionObject(Struct):
	ob_base = field(PyObject_p)
	m_ml = field(ctypes.POINTER(PyMethodDef))
	m_self = field(PyObject_p)
	m_module = field(PyObject_p)
	vectorcallfunc = field(vectorcallfunc)


class PyCMethodObject(Struct):
	func = field(PyCFunctionObject)
	mm_class = field(PyTypeObject_p)


# TODO python functions, update_structs
