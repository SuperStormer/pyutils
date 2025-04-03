import ctypes
import sys

from utils.hazmat.misc import get_addr

from .base import Struct, field
from .common import Py_hash_t, PyObject, PyObject_p, PyVarObject, update_types
from .num import PyLongObject


# https://github.com/python/cpython/blob/master/Include/cpython/tupleobject.h
class PyTupleObject(Struct):
	ob_base = field(PyVarObject)
	if sys.version_info >= (3, 14):
		ob_hash = field(Py_hash_t)
	_ob_item = field(PyObject_p * 1)

	@property
	def ob_item(self):
		return self.get_vla("_ob_item", PyObject_p, self.ob_base.ob_size)

	value = ob_item


# https://github.com/python/cpython/blob/master/Include/cpython/listobject.h
class PyListObject(Struct):
	ob_base = field(PyVarObject)
	_ob_item = field(ctypes.POINTER(PyObject_p))
	allocated = field(ctypes.c_ssize_t)

	@property
	def ob_item(self):
		addr = get_addr(self._ob_item)
		assert addr is not None
		return (PyObject_p * self.ob_base.ob_size).from_address(addr)

	value = ob_item


# https://github.com/python/cpython/blob/main/Include/cpython/setobject.h
class setentry(Struct):  # noqa: N801
	key = field(PyObject_p)
	hash = field(Py_hash_t)


class PySetObject(Struct):
	MINSIZE = 8

	ob_base = field(PyObject)
	fill = field(ctypes.c_ssize_t)
	used = field(ctypes.c_ssize_t)
	mask = field(ctypes.c_ssize_t)
	_table = field(ctypes.POINTER(setentry))
	hash = field(Py_hash_t)
	finger = field(ctypes.c_ssize_t)
	smalltable = field(setentry * MINSIZE)
	weakreflist = field(PyObject_p)

	@property
	def table(self):
		addr = get_addr(self._table)
		assert addr is not None
		return (setentry * (self.mask + 1)).from_address(addr)

	value = table


# https://github.com/python/cpython/blob/master/Objects/rangeobject.c
class rangeobject(Struct):  # noqa: N801
	ob_base = field(PyObject)
	_start = field(PyObject_p)
	_stop = field(PyObject_p)
	_step = field(PyObject_p)
	_length = field(PyObject_p)


for _field in ["start", "stop", "step", "length"]:

	@property
	def _get(self, field=_field):  # noqa: PLR0206
		return ctypes.cast(getattr(self, "_" + field), ctypes.POINTER(PyLongObject))[0]

	setattr(rangeobject, _field, _get)
del _field
del _get

update_types({
	list: PyListObject,
	tuple: PyTupleObject,
	set: PySetObject,
	frozenset: PySetObject,
	range: rangeobject,
})
