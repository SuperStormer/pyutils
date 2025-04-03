import ctypes

from utils.hazmat.structs.base import Struct
from utils.hazmat.structs.common import (
	PyMethodDef,
	PyObject_p,
	PyTypeObject_p,
	vectorcallfunc,
)


# https://github.com/python/cpython/blob/main/Include/cpython/methodobject.h
class PyCFunctionObject(Struct):
	_fields_ = [
		("ob_base", PyObject_p),
		("m_ml", ctypes.POINTER(PyMethodDef)),
		("m_self", PyObject_p),
		("m_module", PyObject_p),
		("vectorcallfunc", vectorcallfunc),
	]


class PyCMethodObject(Struct):
	_fields_ = [("func", PyCFunctionObject), ("mm_class", PyTypeObject_p)]


# TODO python functions, update_structs
