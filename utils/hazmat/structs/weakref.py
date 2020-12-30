import weakref
import ctypes
from .base import Struct
from .common import PyObject, PyObject_p, Py_hash_t, update_types

#https://github.com/python/cpython/blob/master/Include/weakrefobject.h
class PyWeakReference(Struct):
	@property
	def value(self):
		return self.wr_object

PyWeakReference._fields_ = [ #pylint: disable=protected-access
	("ob_base", PyObject), ("wr_object", PyObject_p), ("wr_callback", PyObject_p),
	("hash", Py_hash_t), ("wr_prev", ctypes.POINTER(PyWeakReference)),
	("wr_next", ctypes.POINTER(PyWeakReference))
]

update_types({weakref.ref: PyWeakReference})
