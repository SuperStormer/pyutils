import ctypes
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
	import _ctypes
	from typing import TypeVar

	T = TypeVar("T")
	U = TypeVar(
		"U",
		bound=_ctypes._Pointer[Any]  # noqa: SLF001
		| _ctypes.CFuncPtr
		| _ctypes.Union
		| _ctypes.Structure
		| _ctypes.Array[Any],
	)


@dataclass
class Field:
	type: type
	bit_width: int | None


@overload
def field(
	c_type: "type[ctypes._SimpleCData[T]]", bit_width: int | None = None
) -> "T": ...
@overload
def field(c_type: "type[U]", bit_width: int | None = None) -> "U": ...
def field(c_type: "type[ctypes._CDataType]", bit_width: int | None = None) -> Any:
	return Field(c_type, bit_width)


def field_alias(field: str, c_type: "type[ctypes._CDataType]"):
	def getter(self):
		return ctypes.cast(getattr(self, field), ctypes.POINTER(c_type)).contents

	return property(getter)


def init_fields(cls):
	fields = [
		(
			(key, value.type, value.bit_width)
			if value.bit_width is not None
			else (key, value.type)
		)
		for key, value in cls.__dict__.items()
		if isinstance(value, Field)
	]
	if fields:
		cls._fields_ = fields


class StructMeta(type(ctypes.Structure)):
	def __init__(cls, name, base, attrs):
		super().__init__(name, base, attrs)
		init_fields(cls)


class Struct(ctypes.Structure, metaclass=StructMeta):
	def __repr__(self):
		cls = type(self)
		field_reprs = []
		for field in cls._fields_:
			attr = field[0]
			if attr.startswith("_") and hasattr(self, attr[1:]):
				attr = attr[1:]
			val = getattr(self, attr)
			field_reprs.append(f"{attr}={val}")
		return f"{cls.__name__}(\n{',\n'.join(field_reprs)})"

	def get_vla(self, field, typ, size):
		return (typ * size).from_address(
			ctypes.addressof(self) + getattr(type(self), field).offset
		)

	@classmethod
	def from_object(cls, obj):
		"""converts from python object to a struct"""
		return cls.from_address(id(obj))

	def to_object(self):
		"""converts struct to python object"""
		return ctypes.cast(ctypes.byref(self), ctypes.py_object).value

	def __getattr__(self, name: str):
		if name != "ob_base":
			try:
				return getattr(self.ob_base, name)
			except AttributeError:
				pass
		raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

	def __setattr__(self, name: str, value):
		try:
			object.__getattribute__(self, name)
		except AttributeError as e:
			try:
				setattr(self.ob_base, name, value)
			except AttributeError:
				raise e from None
		else:
			object.__setattr__(self, name, value)


class UnionMeta(type(ctypes.Union)):
	def __init__(cls, name, base, attrs):
		super().__init__(name, base, attrs)
		init_fields(cls)


class Union(ctypes.Union, metaclass=UnionMeta):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(
			f"{field[0]}={getattr(self, field[0])}" for field in cls._fields_
		)
		return f"{cls.__name__}(\n{fields})"
