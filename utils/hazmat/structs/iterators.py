# ruff: noqa: N801
import ctypes
import sys

from .base import Struct
from .collections import PyListObject, PySetObject, PyTupleObject
from .common import PyObject, PyObject_p, update_types
from .dict import PyDictObject
from .num import PyLongObject


# https://github.com/python/cpython/blob/master/Objects/iterobject.c
class seqiterobject(Struct):
	"""
	A sequence iterator, works with an arbitrary sequence
	supporting the __getitem__() method.
	(from https://docs.python.org/3/c-api/iterator.html)
	"""

	_fields_ = [
		("ob_base", PyObject),
		("it_index", ctypes.c_ssize_t),
		("it_seq", PyObject_p),
	]

	@property
	def value(self):
		return self.it_seq[0]

	@classmethod
	def from_seq(cls, seq):
		return PySeqIter_New(seq)[0]


PySeqIter_New = ctypes.pythonapi.PySeqIter_New
PySeqIter_New.argtypes = [ctypes.py_object]
PySeqIter_New.restype = ctypes.POINTER(seqiterobject)


class calliterobject(Struct):
	"""
	A callable iterator, works with a callable object and a sentinel value,
	calling the callable for each item in the sequence,
	and ending the iteration when the sentinel value is returned.
	(from https://docs.python.org/3/c-api/iterator.html)
	"""

	_fields_ = [
		("ob_base", PyObject),
		("it_callable", PyObject_p),
		("it_sentinel", PyObject_p),
	]

	@property
	def callable(self):
		return ctypes.cast(self.it_callable, ctypes.py_object).value

	value = callable


# https://github.com/python/cpython/blob/master/Objects/listobject.c
class PyListIterObject(Struct):
	_fields_ = [
		("ob_base", PyObject),
		("it_index", ctypes.c_ssize_t),
		("it_seq", ctypes.POINTER(PyListObject)),
	]

	@property
	def value(self):
		return self.it_seq[0]


# https://github.com/python/cpython/blob/main/Include/internal/pycore_tuple.h
class PyTupleIterObject(Struct):
	_fields_ = [
		("ob_base", PyObject),
		("it_index", ctypes.c_ssize_t),
		("it_seq", ctypes.POINTER(PyTupleObject)),
	]

	@property
	def value(self):
		return self.it_seq[0]


# https://github.com/python/cpython/blob/master/Objects/setobject.c
class setiterobject(Struct):
	_fields_ = [
		("ob_base", PyObject),
		("si_set", ctypes.POINTER(PySetObject)),
		("si_used", ctypes.c_ssize_t),
		("si_pos", ctypes.c_ssize_t),
		("len", ctypes.c_ssize_t),
	]

	@property
	def value(self):
		return self.si_set[0]


# https://github.com/python/cpython/blob/master/Objects/dictobject.c
class dictiterobject(Struct):
	_fields_ = [
		("ob_base", PyObject),
		("di_dict", ctypes.POINTER(PyDictObject)),
		("di_used", ctypes.c_ssize_t),
		("di_pos", ctypes.c_ssize_t),
		("di_result", PyObject_p),
		("len", ctypes.c_ssize_t),
	]

	@property
	def value(self):
		return self.di_dict[0]


# https://github.com/python/cpython/blame/main/Include/internal/pycore_range.h
class PyRangeIterObject(Struct):
	_fields_ = [
		("ob_base", PyObject),
		("index", ctypes.c_long),
		("start", ctypes.c_long),
		("stop", ctypes.c_long),
		("step", ctypes.c_long),
		("length", ctypes.c_long),
	]


# https://github.com/python/cpython/blame/main/Objects/rangeobject.c
class longrangeiterobject(Struct):
	_fields_ = [
		("ob_base", PyObject),
		("_start", PyObject_p),
		("_step", PyObject_p),
		("_len", PyObject_p),
	]


for _field in ["index", "start", "stop", "step", "length"]:

	@property
	def _get(self, field=_field):  # noqa: PLR0206
		return ctypes.cast(getattr(self, "_" + field), ctypes.POINTER(PyLongObject))[0]

	setattr(longrangeiterobject, _field, _get)
del _field
del _get


# https://github.com/python/cpython/blob/master/Python/bltinmodule.c
class filterobject(Struct):
	_fields_ = [("ob_base", PyObject), ("func", PyObject_p), ("it", PyObject_p)]

	@property
	def value(self):
		return self.it


class mapobject(Struct):
	if sys.version_info >= (3, 14):
		_fields_ = [
			("ob_base", PyObject),
			("iters", PyObject_p),
			("func", PyObject_p),
			("strict", ctypes.c_int),
		]
	else:
		_fields_ = [("ob_base", PyObject), ("iters", PyObject_p), ("func", PyObject_p)]

	@property
	def value(self):
		return self.iters


class zipobject(Struct):
	if sys.version_info >= (3, 10):
		_fields_ = [
			("ob_base", PyObject),
			("tuplesize", ctypes.c_ssize_t),
			("_ittuple", PyObject_p),
			("_result", PyObject_p),
			("strict", ctypes.c_int),
		]
	else:
		_fields_ = [
			("ob_base", PyObject),
			("tuplesize", ctypes.c_ssize_t),
			("_ittuple", PyObject_p),
			("_result", PyObject_p),
		]

	@property
	def ittuple(self):
		return ctypes.cast(self._ittuple, ctypes.POINTER(PyTupleObject))[0]

	@property
	def result(self):
		return ctypes.cast(self._result, ctypes.POINTER(PyTupleObject))[0]

	value = ittuple


# https://github.com/python/cpython/blob/master/Objects/enumobject.c
class enumobject(Struct):
	"""enumerate()"""

	_fields_ = [
		("ob_base", PyObject),
		("en_index", ctypes.c_ssize_t),
		("en_sit", PyObject_p),
		("_en_result", PyObject_p),
		("_en_longindex", PyObject_p),
	]
	if sys.version_info >= (3, 11):
		_fields_ = [
			("ob_base", PyObject),
			("en_index", ctypes.c_ssize_t),
			("en_sit", PyObject_p),
			("_en_result", PyObject_p),
			("_en_longindex", PyObject_p),
			("one", PyObject_p),
		]
	else:
		_fields_ = [
			("ob_base", PyObject),
			("en_index", ctypes.c_ssize_t),
			("en_sit", PyObject_p),
			("_en_result", PyObject_p),
			("_en_longindex", PyObject_p),
		]

	@property
	def en_result(self):
		return ctypes.cast(self._en_result, ctypes.POINTER(PyTupleObject))[0]

	@property
	def en_longindex(self):
		return ctypes.cast(self._en_longindex, ctypes.POINTER(PyLongObject))[0]

	@property
	def value(self):
		return self.en_sit


class reversedobject(Struct):
	_fields_ = [("ob_base", PyObject), ("index", ctypes.c_ssize_t), ("seq", PyObject_p)]

	@property
	def value(self):
		return self.seq


# used to find seqiterobject's addr
class _A:  # pylint: disable=too-few-public-methods
	def __getitem__(self, val):
		pass


update_types({
	type(iter(lambda: None, None)): calliterobject,
	type(iter(_A())): seqiterobject,
	type(iter([])): PyListIterObject,
	type(iter(())): PyTupleIterObject,
	type(iter(set())): setiterobject,
	type(iter({})): dictiterobject,
	type(iter(range(0))): PyRangeIterObject,
	type(iter(range(2**63))): longrangeiterobject,
	filter: filterobject,
	map: mapobject,
	zip: zipobject,
	enumerate: enumobject,
	reversed: reversedobject,
})

del _A
