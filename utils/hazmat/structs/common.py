import ctypes
import sys
from enum import Enum, Flag
from typing import NamedTuple, Type

from utils.hazmat.misc import get_addr

from .base import Struct, field

Py_hash_t = ctypes.c_ssize_t  # pylint: disable=invalid-name
Py_ssize_t = ctypes.c_ssize_t  # pylint: disable=invalid-name

# https://github.com/python/cpython/blob/master/Include/object.h
# define PyObject_HEAD          PyObject ob_base;
# define PyObject_VAR_HEAD      PyVarObject ob_base;


class PyObject(Struct):
	def get_type(self):
		addr = get_addr(self.ob_type)
		if addr is None:
			raise ValueError("ob_type is a null pointer")
		return type_dict[addr].type

	def get_struct_type(self):
		addr = get_addr(self.ob_type)
		if addr is None:
			raise ValueError("ob_type is a null pointer")
		return type_dict[addr].struct

	def get_real(self):
		return self.get_struct_type().from_address(ctypes.addressof(self))


# https://github.com/python/cpython/blob/main/Doc/includes/typestruct.h
# can't be moved to a separate module because that causes errors due to codependency
class PyTypeObject(Struct):
	class Flags(Flag):
		# Set if the type object is dynamically allocated
		HEAPTYPE = 1 << 9
		# Set if the type allows subclassing
		BASETYPE = 1 << 10
		# Set if the type implements the vectorcall protocol (PEP 590)
		HAVE_VECTORCALL = 1 << 11
		# Set if the type is "ready" -- fully initialized
		READY = 1 << 12
		# Set while the type is being "readied", to prevent recursive ready calls
		READYING = 1 << 13
		# Objects support garbage collection (see objimpl.h)
		HAVE_GC = 1 << 14
		# Objects behave like an unbound method
		METHOD_DESCRIPTOR = 1 << 17
		# Objects support type attribute cache
		HAVE_VERSION_TAG = 1 << 18
		VALID_VERSION_TAG = 1 << 19
		# Type is abstract and cannot be instantiated
		IS_ABSTRACT = 1 << 20
		# Type has am_send entry in tp_as_async slot
		HAVE_AM_SEND = 1 << 21
		# These flags are used to determine if a type is a subclass.
		LONG_SUBCLASS = 1 << 24
		LIST_SUBCLASS = 1 << 25
		TUPLE_SUBCLASS = 1 << 26
		BYTES_SUBCLASS = 1 << 27
		UNICODE_SUBCLASS = 1 << 28
		DICT_SUBCLASS = 1 << 29
		BASE_EXC_SUBCLASS = 1 << 30
		TYPE_SUBCLASS = 1 << 31

		DEFAULT = HAVE_VERSION_TAG

	@property
	def tp_flags(self):
		return PyTypeObject.Flags(self._tp_flags)

	def get_type(self):
		return type_dict[ctypes.addressof(self)][0]

	def get_struct_type(self):
		return type_dict[ctypes.addressof(self)][1]


PyTypeObject_p = ctypes.POINTER(PyTypeObject)
PyObject_p = ctypes.POINTER(PyObject)

# Add the two extra fields to PyObject by relying on _Py_ForgetReference to see if Py_TRACE_REFS is defined
# credit to Crowthebird#1649 (<@!675937585624776717>)
if hasattr(ctypes.pythonapi, "_Py_ForgetReference"):
	PyObject._fields_ = [
		("_ob_next", PyObject_p),
		("_ob_prev", PyObject_p),
		("ob_refcnt", ctypes.c_ssize_t),
		("ob_type", PyTypeObject_p),
	]
else:
	# TODO: ob_refcnt is a union now
	PyObject._fields_ = [("ob_refcnt", ctypes.c_ssize_t), ("ob_type", PyTypeObject_p)]


# https://github.com/python/cpython/blob/main/Include/object.h
class PyVarObject(Struct):
	ob_base = field(PyObject)
	ob_size = field(ctypes.c_ssize_t)


# https://github.com/python/cpython/blob/main/Include/pybuffer.h
class Py_buffer(Struct):  # noqa: N801
	buf = field(ctypes.c_void_p)
	obj = field(PyObject_p)  # owned ref
	len = field(ctypes.c_ssize_t)
	itemsize = field(ctypes.c_ssize_t)
	readonly = field(ctypes.c_int)
	ndim = field(ctypes.c_int)
	format = field(ctypes.c_char_p)
	shape = field(ctypes.POINTER(ctypes.c_ssize_t))
	strides = field(ctypes.POINTER(ctypes.c_ssize_t))
	suboffsets = field(ctypes.POINTER(ctypes.c_ssize_t))
	internal = field(ctypes.c_void_p)


# https://github.com/python/cpython/blob/main/Include/object.h
unaryfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)
binaryfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object)
ternaryfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.py_object
)
inquiry = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object)
lenfunc = ctypes.PYFUNCTYPE(ctypes.c_ssize_t, ctypes.py_object)

ssizeargfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.c_ssize_t)
ssizeobjargproc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.c_ssize_t, ctypes.py_object
)
objobjargproc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.py_object
)

objobjproc = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, ctypes.py_object)
visitproc = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, ctypes.c_void_p)
traverseproc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, visitproc, ctypes.c_void_p
)

freefunc = ctypes.PYFUNCTYPE(None, ctypes.c_void_p)
destructor = ctypes.PYFUNCTYPE(None, ctypes.py_object)

getattrfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.c_char_p)
getattrofunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object)
setattrfunc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.c_char_p, ctypes.py_object
)
setattrofunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.c_char_p, ctypes.py_object
)

reprfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)
hashfunc = ctypes.PYFUNCTYPE(Py_hash_t, ctypes.py_object)
richcmpfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.c_int
)

getiterfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)
iternextfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)

descrgetfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.py_object
)
descrsetfunc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.py_object
)

initproc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.py_object
)
newfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.py_object
)
allocfunc = ctypes.PYFUNCTYPE(ctypes.py_object, PyTypeObject_p, ctypes.c_ssize_t)

PySendResult = ctypes.c_uint  # actually an enum
sendfunc = ctypes.PYFUNCTYPE(
	PySendResult, ctypes.py_object, ctypes.py_object, ctypes.POINTER(ctypes.py_object)
)
vectorcallfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object,
	ctypes.py_object,
	ctypes.POINTER(ctypes.py_object),
	ctypes.c_size_t,
	ctypes.py_object,
)
getbufferproc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.POINTER(Py_buffer), ctypes.c_int
)
releasebufferproc = ctypes.PYFUNCTYPE(None, ctypes.py_object, ctypes.POINTER(Py_buffer))


# https://github.com/python/cpython/blob/main/Include/cpython/object.h
class PyNumberMethods(Struct):
	# normal ops
	nb_add = field(binaryfunc)
	nb_subtract = field(binaryfunc)
	nb_multiply = field(binaryfunc)
	nb_remainder = field(binaryfunc)
	nb_divmod = field(binaryfunc)
	nb_power = field(binaryfunc)
	nb_negative = field(unaryfunc)
	nb_positive = field(unaryfunc)
	nb_absolute = field(unaryfunc)
	nb_bool = field(inquiry)
	nb_invert = field(unaryfunc)
	nb_lshift = field(binaryfunc)
	nb_rshift = field(binaryfunc)
	nb_and = field(binaryfunc)
	nb_xor = field(binaryfunc)
	nb_or = field(binaryfunc)
	nb_int = field(unaryfunc)
	nb_reserved = field(ctypes.c_void_p)  # used to be nb_long
	nb_float = field(unaryfunc)
	# inplace ops
	nb_inplace_add = field(binaryfunc)
	nb_inplace_subtract = field(binaryfunc)
	nb_inplace_multiply = field(binaryfunc)
	nb_inplace_remainder = field(binaryfunc)
	nb_inplace_power = field(ternaryfunc)
	nb_inplace_lshift = field(binaryfunc)
	nb_inplace_rshift = field(binaryfunc)
	nb_inplace_and = field(binaryfunc)
	nb_inplace_xor = field(binaryfunc)
	nb_inplace_or = field(binaryfunc)
	# division
	nb_floor_divide = field(binaryfunc)
	nb_true_divide = field(binaryfunc)
	nb_inplace_floor_divide = field(binaryfunc)
	nb_inplace_true_divide = field(binaryfunc)
	# __index__()
	nb_index = field(unaryfunc)
	# matmul
	nb_matrix_multiply = field(binaryfunc)
	nb_inplace_matrix_multiply = field(binaryfunc)


# https://github.com/python/cpython/blob/main/Include/cpython/object.h
class PySequenceMethods(Struct):
	sq_length = field(lenfunc)
	sq_concat = field(binaryfunc)
	sq_repeat = field(ssizeargfunc)
	sq_item = field(ssizeargfunc)
	was_sq_slice = field(ctypes.c_void_p)
	sq_ass_item = field(ssizeobjargproc)
	was_sq_ass_slice = field(ctypes.c_void_p)
	sq_contains = field(objobjproc)
	sq_inplace_concat = field(binaryfunc)
	sq_inplace_repeat = field(ssizeargfunc)


# https://github.com/python/cpython/blob/main/Include/cpython/object.h
class PyMappingMethods(Struct):
	mp_length = field(lenfunc)
	mp_subscript = field(binaryfunc)
	mp_ass_subscript = field(objobjproc)


# https://github.com/python/cpython/blob/main/Include/cpython/object.h
class PyAsyncMethods(Struct):
	am_await = field(unaryfunc)
	am_aiter = field(unaryfunc)
	am_anext = field(unaryfunc)
	am_send = field(sendfunc)


# https://github.com/python/cpython/blob/main/Include/cpython/object.h
class PyBufferProcs(Struct):
	bf_getbuffer = field(getbufferproc)
	bf_releasebuffer = field(releasebufferproc)


# https://github.com/python/cpython/blob/main/Include/methodobject.h
PyCFunction = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)
PyCFunctionFast = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.c_ssize_t)
PyCFunctionWithKeywords = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.py_object
)
PyCFunctionFastWithKeywords = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.c_ssize_t, ctypes.py_object
)
PyCMethod = ctypes.PYFUNCTYPE(
	ctypes.py_object, PyTypeObject_p, ctypes.py_object, ctypes.c_ssize_t, ctypes.py_object
)


# https://github.com/python/cpython/blob/main/Include/methodobject.h
class PyMethodDef(Struct):
	ml_name = field(ctypes.c_char_p)
	ml_meth = field(PyCFunction)
	ml_flags = field(ctypes.c_int)  # TODO turn this into a Flag
	ml_doc = field(ctypes.c_char_p)


# https://github.com/python/cpython/blob/main/Include/descrobject.h
class PyMemberDef(Struct):
	# https://github.com/python/cpython/blob/main/Include/structmember.h
	class Type(Enum):
		SHORT = 0
		INT = 1
		LONG = 2
		FLOAT = 3
		DOUBLE = 4
		STRING = 5
		OBJECT = 6
		CHAR = 7  # 1-character string
		BYTE = 8  # 8-bit signed int
		# unsigned variants:
		UBYTE = 9
		USHORT = 10
		UINT = 11
		ULONG = 12

		# strings contained in the structure
		STRING_INPLACE = 13

		# bools contained in the structure (assumed char)
		BOOL = 14
		# ike T_OBJECT, but raises AttributeError
		# when the value is NULL, instead of converting to None.
		OBJECT_EX = 16
		LONGLONG = 17
		ULONGLONG = 18

		PYSSIZET = 19
		NONE = 20

	class Flags(Flag):
		READONLY = 1
		READ_RESTRICTED = 2
		PY_WRITE_RESTRICTED = 4
		RESTRICTED = READ_RESTRICTED | PY_WRITE_RESTRICTED

	name = field(ctypes.c_char_p)
	_type = field(ctypes.c_int)
	offset = field(ctypes.c_ssize_t)
	_flags = field(ctypes.c_int)
	doc = field(ctypes.c_char_p)

	@property
	def type(self):
		return PyMemberDef.Type(self._type)

	@property
	def flags(self):
		return PyMemberDef.Flags(self._flags)


# https://github.com/python/cpython/blob/master/Include/descrobject.h
getter = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.c_void_p)
setter = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.c_void_p
)


# https://github.com/python/cpython/blob/master/Include/descrobject.h
class PyGetSetDef(Struct):
	name = field(ctypes.c_char_p)
	get = field(getter)
	set = field(setter)
	doc = field(ctypes.c_char_p)
	closure = field(ctypes.c_void_p)


# type object fields
_fields = [  # noqa: SLF001
	("ob_base", PyVarObject),
	("tp_name", ctypes.c_char_p),
	# for allocation
	("tp_basicsize", ctypes.c_ssize_t),
	("tp_itemsize", ctypes.c_ssize_t),
	# standard ops
	("tp_dealloc", destructor),
	("tp_vectorcall_offset", ctypes.c_ssize_t),  # used to be printfunc
	("tp_getattr", getattrfunc),
	("tp_setattr", setattrfunc),
	("tp_as_async", ctypes.POINTER(PyAsyncMethods)),
	("tp_repr", reprfunc),
	# methods for standard classes
	("tp_as_number", ctypes.POINTER(PyNumberMethods)),
	("tp_as_sequence", ctypes.POINTER(PySequenceMethods)),
	("tp_as_mapping", ctypes.POINTER(PyMappingMethods)),
	# more standard ops
	("tp_hash", hashfunc),
	("tp_call", ternaryfunc),
	("tp_str", reprfunc),
	("tp_getattro", getattrofunc),
	("tp_setattro", setattrofunc),
	# get as IO buffer
	("tp_as_buffer", ctypes.POINTER(PyBufferProcs)),
	# feature flags
	("_tp_flags", ctypes.c_ulong),
	# docstring
	("tp_doc", ctypes.c_char_p),
	# misc
	("tp_traverse", traverseproc),
	("tp_clear", inquiry),
	("tp_richcompare", richcmpfunc),
	("tp_weaklistoffset", ctypes.c_ssize_t),
	("tp_iter", getiterfunc),
	("tp_iternext", iternextfunc),
	("tp_methods", ctypes.POINTER(PyMethodDef)),
	("tp_members", ctypes.POINTER(PyMemberDef)),
	("tp_getset", ctypes.POINTER(PyGetSetDef)),
	("tp_base", PyTypeObject_p),
	("tp_dict", PyObject_p),
	("tp_descr_get", descrgetfunc),
	("tp_descr_set", descrsetfunc),
	("tp_dictoffset", ctypes.c_ssize_t),
	# instance creation/deletion
	("tp_init", initproc),
	("tp_alloc", allocfunc),
	("tp_new", newfunc),
	("tp_free", freefunc),
	("tp_is_gc", inquiry),
	("tp_bases", PyObject_p),
	("tp_mro", PyObject_p),
	("tp_cache", PyObject_p),
	("tp_subclasses", PyObject_p),
	("tp_weaklist", PyObject_p),
	("tp_del", destructor),
	("tp_version_tag", ctypes.c_uint),
	("tp_finalize", destructor),
]
if sys.version_info >= (3, 10):
	_fields.append(("tp_vectorcall", vectorcallfunc))
if sys.version_info >= (3, 12):
	_fields.append(("tp_watched", ctypes.c_ubyte))


PyTypeObject._fields_ = _fields
del _fields


# type handling utils
class TypeLookup(NamedTuple):
	type: type
	struct: Type[Struct] | None


# id(type): (type,Struct)
type_dict: dict[int, TypeLookup] = {
	id(t): TypeLookup(t, None) for t in object.__subclasses__()
}


def update_types(types: dict[type, type[Struct]]):
	"""updates type_dict with dict of {type: Struct}"""
	type_dict.update({id(t[0]): TypeLookup(*t) for t in types.items()})


update_types({type: PyTypeObject})


def get_struct(val):
	"""returns a Struct for a python object"""
	obj = PyObject.from_object(val)
	try:
		return obj.get_struct_type().from_object(val)
	except (KeyError, AttributeError):
		return obj


# GIL-free types
# https://github.com/python/cpython/blob/main/Include/cpython/lock.h
class PyMutex(Struct):
	_bits = field(ctypes.c_uint8)


Py_GIL_DISABLED = sys.version_info >= (3, 13) and not sys._is_gil_enabled()  # noqa: SLF001

# heap type objects
from .dict import PyDictKeysObject  # noqa: E402


# https://github.com/python/cpython/blob/master/Include/cpython/object.h
class PyHeapTypeObject(Struct):
	ht_type = field(PyTypeObject)
	as_async = field(PyAsyncMethods)
	as_number = field(PyNumberMethods)
	as_mapping = field(PyMappingMethods)
	as_sequence = field(PySequenceMethods)
	as_buffer = field(PyBufferProcs)
	ht_name = field(PyObject_p)
	ht_slots = field(PyObject_p)
	ht_qualname = field(PyObject_p)
	ht_cached_keys = field(ctypes.POINTER(PyDictKeysObject))

	# TODO update


# misc
Py_None = PyObject.from_address(id(None))
Py_Ellipsis = PyObject.from_address(id(Ellipsis))
Py_NotImplemented = PyObject.from_address(id(NotImplemented))
