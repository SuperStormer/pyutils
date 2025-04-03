import ctypes
import sys
import weakref

from .base import Struct
from .common import (
	Py_GIL_DISABLED,
	Py_hash_t,
	PyMutex,
	PyObject,
	PyObject_p,
	update_types,
	vectorcallfunc,
)


# https://github.com/python/cpython/blob/main/Include/cpython/weakrefobject.h
class PyWeakReference(Struct):
	@property
	def value(self):
		return self.wr_object


_fields = [
	("ob_base", PyObject),
	("wr_object", PyObject_p),
	("wr_callback", PyObject_p),
	("hash", Py_hash_t),
	("wr_prev", ctypes.POINTER(PyWeakReference)),
	("wr_next", ctypes.POINTER(PyWeakReference)),
]
if sys.version_info >= (3, 11):
	_fields += [
		("vectorcall", vectorcallfunc),
	]
if Py_GIL_DISABLED:
	_fields += [
		("weakrefs_lock", ctypes.POINTER(PyMutex)),
	]
PyWeakReference._fields_ = _fields
del _fields

update_types({weakref.ref: PyWeakReference})
