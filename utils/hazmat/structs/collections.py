import ctypes
import sys

from utils.hazmat.misc import get_addr

from .base import Struct, field, field_alias
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
		if addr is None:
			raise ValueError("ob_item is a null pointer")
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
		if addr is None:
			raise ValueError("table is a null pointer")
		return (setentry * (self.mask + 1)).from_address(addr)

	value = table


# https://github.com/python/cpython/blob/master/Objects/rangeobject.c
class rangeobject(Struct):  # noqa: N801
	ob_base = field(PyObject)
	_start = field(PyObject_p)
	_stop = field(PyObject_p)
	_step = field(PyObject_p)
	_length = field(PyObject_p)

	start = field_alias("_start", PyLongObject)
	stop = field_alias("_stop", PyLongObject)
	step = field_alias("_step", PyLongObject)
	length = field_alias("_length", PyLongObject)


update_types({
	list: PyListObject,
	tuple: PyTupleObject,
	set: PySetObject,
	frozenset: PySetObject,
	range: rangeobject,
})
