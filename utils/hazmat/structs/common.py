import ctypes
from enum import Enum, Flag
from typing import NamedTuple, Optional, Type

from utils.hazmat.misc import get_addr

from .base import Struct

Py_hash_t = ctypes.c_ssize_t  #pylint: disable=invalid-name
Py_ssize_t = ctypes.c_ssize_t  #pylint: disable=invalid-name

# https://github.com/python/cpython/blob/master/Include/object.h
#define PyObject_HEAD          PyObject ob_base;
#define PyObject_VAR_HEAD      PyVarObject ob_base;

class PyObject(Struct):
	def get_type(self):
		return type_dict[get_addr(self.ob_type)].type
	
	def get_struct_type(self):
		return type_dict[get_addr(self.ob_type)].struct
	
	def get_real(self):
		return self.get_struct_type().from_address(ctypes.addressof(self))

# https://github.com/python/cpython/blob/master/Include/cpython/object.h
# and https://github.com/python/cpython/blob/master/Include/object.h
# also based on https://github.com/clarete/forbiddenfruit/blob/master/forbiddenfruit/__init__.py
# PyTypeObject can"t be moved to a separate module because that causes errors due to codependency
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

PyTypeObject_p = ctypes.POINTER(PyTypeObject)  #pylint: disable=invalid-name
PyObject_p = ctypes.POINTER(PyObject)

# Add the two extra fields to PyObject by relying on _Py_ForgetReference to see if Py_TRACE_REFS is defined
# credit to Crowthebird#1649 (<@!675937585624776717>)
if hasattr(ctypes.pythonapi, "_Py_ForgetReference"):
	PyObject._fields_ = [ #pylint: disable=protected-access
		("_ob_next", PyObject_p), ("_ob_prev", PyObject_p), ("ob_refcnt", ctypes.c_ssize_t),
		("ob_type", PyTypeObject_p)
	]
else:
	PyObject._fields_ = [("ob_refcnt", ctypes.c_ssize_t), ("ob_type", PyTypeObject_p)]  #pylint: disable=protected-access

class PyVarObject(Struct):
	_fields_ = [("ob_base", PyObject), ("ob_size", ctypes.c_ssize_t)]

#This is here due to codependencies and I don"t want to trigger some weird error
class Py_buffer(Struct):  #pylint: disable=invalid-name
	_fields_ = [
		("buf", ctypes.c_void_p),
		("obj", PyObject_p),  #owned ref
		("len", ctypes.c_ssize_t),
		("itemsize", ctypes.c_ssize_t),
		("readonly", ctypes.c_int),
		("ndim", ctypes.c_int),
		("format", ctypes.c_char_p),
		("shape", ctypes.POINTER(ctypes.c_ssize_t)),
		("strides", ctypes.POINTER(ctypes.c_ssize_t)),
		("suboffsets", ctypes.POINTER(ctypes.c_ssize_t)),
		("internal", ctypes.c_void_p)
	]

# bunch of funcs that the following classes use
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
traverseproc = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, visitproc, ctypes.c_void_p)

freefunc = ctypes.PYFUNCTYPE(None, ctypes.c_void_p)
destructor = ctypes.PYFUNCTYPE(None, ctypes.py_object)

getattrfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.c_char_p)
getattrofunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object)
setattrfunc = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, ctypes.c_char_p, ctypes.py_object)
setattrofunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.c_char_p, ctypes.py_object
)

reprfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)
hashfunc = ctypes.PYFUNCTYPE(Py_hash_t, ctypes.py_object)
richcmpfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.c_int)

getiterfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)
iternextfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object)

descrgetfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.py_object
)
descrsetfunc = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.py_object)

initproc = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.py_object)
newfunc = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.py_object, ctypes.py_object)
allocfunc = ctypes.PYFUNCTYPE(ctypes.py_object, PyTypeObject_p, ctypes.c_ssize_t)

PySendResult = ctypes.c_uint  # actually an enum
sendfunc = ctypes.PYFUNCTYPE(
	PySendResult, ctypes.py_object, ctypes.py_object, ctypes.POINTER(ctypes.py_object)
)
vectorcallfunc = ctypes.PYFUNCTYPE(
	ctypes.py_object, ctypes.py_object, ctypes.POINTER(ctypes.py_object), ctypes.c_size_t,
	ctypes.py_object
)
getbufferproc = ctypes.PYFUNCTYPE(
	ctypes.c_int, ctypes.py_object, ctypes.POINTER(Py_buffer), ctypes.c_int
)
releasebufferproc = ctypes.PYFUNCTYPE(None, ctypes.py_object, ctypes.POINTER(Py_buffer))

class PyNumberMethods(Struct):
	_fields_ = [
		# normal ops
		("nb_add", binaryfunc),
		("nb_subtract", binaryfunc),
		("nb_multiply", binaryfunc),
		("nb_remainder", binaryfunc),
		("nb_divmod", binaryfunc),
		("nb_power", binaryfunc),
		("nb_negative", unaryfunc),
		("nb_positive", unaryfunc),
		("nb_absolute", unaryfunc),
		("nb_bool", inquiry),
		("nb_invert", unaryfunc),
		("nb_lshift", binaryfunc),
		("nb_rshift", binaryfunc),
		("nb_and", binaryfunc),
		("nb_xor", binaryfunc),
		("nb_or", binaryfunc),
		("nb_int", unaryfunc),
		("nb_reserved", ctypes.c_void_p),  # used to be nb_long 
		("nb_float", unaryfunc),
		# inplace ops
		("nb_inplace_add", binaryfunc),
		("nb_inplace_subtract", binaryfunc),
		("nb_inplace_multiply", binaryfunc),
		("nb_inplace_remainder", binaryfunc),
		("nb_inplace_power", ternaryfunc),
		("nb_inplace_lshift", binaryfunc),
		("nb_inplace_rshift", binaryfunc),
		("nb_inplace_and", binaryfunc),
		("nb_inplace_xor", binaryfunc),
		("nb_inplace_or", binaryfunc),
		# division
		("nb_floor_divide", binaryfunc),
		("nb_true_divide", binaryfunc),
		("nb_inplace_floor_divide", binaryfunc),
		("nb_inplace_true_divide", binaryfunc),
		# __index__()
		("nb_index", unaryfunc),
		# matmul
		("nb_matrix_multiply", binaryfunc),
		("nb_inplace_matrix_multiply", binaryfunc),
	]

class PySequenceMethods(Struct):
	_fields_ = [
		("sq_length", lenfunc),
		("sq_concat", binaryfunc),
		("sq_repeat", ssizeargfunc),
		("sq_item", ssizeargfunc),
		("was_sq_slice", ctypes.c_void_p),
		("sq_ass_item", ssizeobjargproc),
		("was_sq_ass_slice", ctypes.c_void_p),
		("sq_contains", objobjproc),
		("sq_inplace_concat", binaryfunc),
		("sq_inplace_repeat", ssizeargfunc),
	]

class PyMappingMethods(Struct):
	_fields_ = [
		("mp_length", lenfunc), ("mp_subscript", binaryfunc), ("mp_ass_subscript", objobjproc)
	]

class PyAsyncMethods(Struct):
	_fields_ = [
		("am_await", unaryfunc), ("am_aiter", unaryfunc), ("am_anext", unaryfunc),
		("am_send", sendfunc)
	]

class PyBufferProcs(Struct):
	_fields_ = [("bf_getbuffer", getbufferproc), ("bf_releasebuffer", releasebufferproc)]

# https://github.com/python/cpython/blob/master/Include/methodobject.h
class PyMethodDef(Struct):
	_fields_ = [("ml_name", ctypes.c_char_p), ("ml_doc", ctypes.c_char_p)]

# https://github.com/python/cpython/blob/master/Include/structmember.h
class PyMemberDef(Struct):
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
		
		#bools contained in the structure (assumed char)
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
		RESTRICTED = (READ_RESTRICTED | PY_WRITE_RESTRICTED)
	
	_fields_ = [
		("name", ctypes.c_char_p), ("_type", ctypes.c_int), ("offset", ctypes.c_ssize_t),
		("_flags", ctypes.c_int), ("doc", ctypes.c_char_p)
	]
	
	@property
	def type(self):
		return PyMemberDef.Type(self._type)
	
	@property
	def flags(self):
		return PyMemberDef.Flags(self._flags)

# https://github.com/python/cpython/blob/master/Include/descrobject.h
getter = ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.py_object, ctypes.c_void_p)
setter = ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.py_object, ctypes.py_object, ctypes.c_void_p)

class PyGetSetDef(Struct):
	_fields_ = [
		("name", ctypes.c_char_p), ("get", getter), ("set", setter), ("doc", ctypes.c_char_p),
		("closure", ctypes.c_void_p)
	]

#type object fields
PyTypeObject._fields_ = [ #pylint: disable=protected-access
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
	#docstring
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
	("tp_vectorcall", vectorcallfunc)

]

#type handling utils
class TypeLookup(NamedTuple):
	type: type
	struct: Optional[Type[Struct]]

# id(type): (type,Struct)
type_dict: dict[int, TypeLookup] = {id(t): TypeLookup(t, None) for t in object.__subclasses__()}

def update_types(types: dict[type, Type[Struct]]):
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

#heap type objects
from .dict import PyDictKeysObject  # pylint: disable=wrong-import-position

class PyHeapTypeObject(Struct):
	_fields_ = [
		("ht_type", PyTypeObject), ("as_async", PyAsyncMethods), ("as_number", PyNumberMethods),
		("as_mapping", PyMappingMethods), ("as_sequence", PySequenceMethods),
		("as_buffer", PyBufferProcs), ("ht_name", PyObject_p), ("ht_slots", PyObject_p),
		("ht_qualname", PyObject_p), ("ht_cached_keys", ctypes.POINTER(PyDictKeysObject))
	]

#misc
Py_None = PyObject.from_address(id(None))
Py_Ellipsis = PyObject.from_address(id(Ellipsis))
Py_NotImplemented = PyObject.from_address(id(NotImplemented))
