import ctypes
import sys

from utils.hazmat.structs.str import PyAsciiObject

from .base import Struct, field, field_alias
from .common import (
	PyMethodDef,
	PyObject,
	PyObject_p,
	PyTypeObject_p,
	update_types,
	vectorcallfunc,
)


# https://github.com/python/cpython/blob/main/Include/cpython/methodobject.h
class PyCFunctionObject(Struct):
	ob_base = field(PyObject_p)
	m_ml = field(ctypes.POINTER(PyMethodDef))
	m_self = field(PyObject_p)
	m_module = field(PyObject_p)
	vectorcallfunc = field(vectorcallfunc)


# https://github.com/python/cpython/blob/main/Include/cpython/methodobject.h
class PyCMethodObject(Struct):
	func = field(PyCFunctionObject)
	mm_class = field(PyTypeObject_p)


# https://github.com/python/cpython/blob/main/Include/cpython/funcobject.h
class PyFunctionObject(Struct):
	ob_base = field(PyObject_p)
	if sys.version_info >= (3, 10):
		func_globals = field(PyObject_p)
		func_builtins = field(PyObject_p)
		_func_name = field(PyObject_p)
		_func_qualname = field(PyObject_p)
		func_code = field(PyObject_p)
		func_defaults = field(PyObject_p)
		func_kwdefaults = field(PyObject_p)
		func_closure = field(PyObject_p)
		func_doc = field(PyObject_p)
		func_dict = field(PyObject_p)
		func_weakreflist = field(PyObject_p)
		func_module = field(PyObject_p)
		func_annotations = field(PyObject_p)
		if sys.version_info >= (3, 14):
			func_annotate = field(PyObject_p)
		if sys.version_info >= (3, 12):
			func_typeparams = field(PyObject_p)
		vectorcall = field(vectorcallfunc)
	else:
		func_code = field(PyObject_p)
		func_globals = field(PyObject_p)
		func_defaults = field(PyObject_p)
		func_kwdefaults = field(PyObject_p)
		func_closure = field(PyObject_p)
		func_doc = field(PyObject_p)
		_func_name = field(PyObject_p)
		func_dict = field(PyObject_p)
		func_weakreflist = field(PyObject_p)
		func_module = field(PyObject_p)
		func_annotations = field(PyObject_p)
		func_qualname = field(PyObject_p)
		vectorcall = field(vectorcallfunc)

	func_name = field_alias("_func_name", PyAsciiObject)
	func_qualname = field_alias("_func_qualname", PyAsciiObject)

	if sys.version_info >= (3, 11):
		func_version = field(ctypes.c_uint32)


# https://github.com/python/cpython/blob/main/Include/cpython/classobject.h
class PyMethodObject(Struct):
	ob_base = field(PyObject)
	im_func = field(PyObject_p)
	im_self = field(PyObject_p)
	im_weakreflist = field(PyObject_p)


class _A:
	def a(self):
		pass


update_types({
	type(all): PyCFunctionObject,
	type(ctypes.c_int.from_param): PyCMethodObject,
	type(update_types): PyFunctionObject,
	type(_A().a): PyMethodObject,
})
del _A
