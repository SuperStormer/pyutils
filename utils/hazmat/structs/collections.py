import ctypes

from utils.hazmat.misc import get_addr

from .base import Struct
from .common import Py_hash_t, PyObject, PyObject_p, PyVarObject, update_types
from .num import PyLongObject


# https://github.com/python/cpython/blob/master/Include/cpython/tupleobject.h
class PyTupleObject(Struct):
	_fields_ = [("ob_base", PyVarObject), ("_ob_item", PyObject_p * 1)]

	@property
	def ob_item(self):
		return self.get_vla("_ob_item", PyObject_p, self.ob_base.ob_size)

	value = ob_item


# https://github.com/python/cpython/blob/master/Include/cpython/listobject.h
class PyListObject(Struct):
	_fields_ = [
		("ob_base", PyVarObject),
		("_ob_item", ctypes.POINTER(PyObject_p)),
		("allocated", ctypes.c_ssize_t),
	]

	@property
	def ob_item(self):
		return (PyObject_p * self.ob_base.ob_size).from_address(get_addr(self._ob_item))

	value = ob_item


# https://github.com/python/cpython/blob/master/Include/setobject.h
class setentry(Struct):  # noqa: N801
	_fields_ = [("key", PyObject_p), ("hash", Py_hash_t)]


class PySetObject(Struct):
	MINSIZE = 8
	_fields_ = [
		("ob_base", PyObject),
		("fill", ctypes.c_ssize_t),
		("used", ctypes.c_ssize_t),
		("mask", ctypes.c_ssize_t),
		("_table", ctypes.POINTER(setentry)),
		("hash", Py_hash_t),
		("finger", ctypes.c_ssize_t),
		("smalltable", (setentry * MINSIZE)),
		("weakreflist", PyObject_p),
	]

	@property
	def table(self):
		return (setentry * (self.mask + 1)).from_address(get_addr(self._table))

	value = table


# https://github.com/python/cpython/blob/master/Objects/rangeobject.c
class rangeobject(Struct):  # noqa: N801
	_fields_ = [
		("ob_base", PyObject),
		("_start", PyObject_p),
		("_stop", PyObject_p),
		("_step", PyObject_p),
		("_length", PyObject_p),
	]


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
