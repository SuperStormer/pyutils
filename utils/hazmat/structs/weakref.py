import ctypes
import weakref

from .base import Struct
from .common import Py_hash_t, PyObject, PyObject_p, update_types


# https://github.com/python/cpython/blob/master/Include/weakrefobject.h
class PyWeakReference(Struct):
	@property
	def value(self):
		return self.wr_object


PyWeakReference._fields_ = [  # noqa: SLF001
	("ob_base", PyObject),
	("wr_object", PyObject_p),
	("wr_callback", PyObject_p),
	("hash", Py_hash_t),
	("wr_prev", ctypes.POINTER(PyWeakReference)),
	("wr_next", ctypes.POINTER(PyWeakReference)),
]

update_types({weakref.ref: PyWeakReference})
