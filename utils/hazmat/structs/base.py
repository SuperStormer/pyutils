import ctypes
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, overload


@dataclass
class Field:
	type: type


@overload
def field(c_type: "type[ctypes._SimpleCData[T]]") -> "T": ...
@overload
def field(c_type: "type[U]") -> "U": ...
def field(c_type: "type[ctypes._CDataType]") -> Any:
	return Field(c_type)


class StructMeta(type(ctypes.Structure)):
	def __init__(cls, name, base, attrs):
		# print(cls, name, base, attrs)
		super().__init__(name, base, attrs)
		fields = [
			(key, value.type)
			for key, value in cls.__dict__.items()
			if isinstance(value, Field)
		]
		if fields:
			print(fields)
			cls._fields_ = [
				(
					name,
					typ,
				)
				for name, typ in fields
			]


class Struct(ctypes.Structure, metaclass=StructMeta):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(
			f"{field[0]}={getattr(self, field[0])}" for field in cls._fields_
		)
		return f"{cls.__name__}(\n{fields})"

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


if TYPE_CHECKING:
	import _ctypes
	from typing import TypeVar

	T = TypeVar("T")
	U = TypeVar(
		"U",
		bound=_ctypes._Pointer[Any]
		| _ctypes.CFuncPtr
		| _ctypes.Union
		| _ctypes.Structure
		| _ctypes.Array[Any],
	)


class Union(ctypes.Union):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(
			f"{field[0]}={getattr(self, field[0])}" for field in cls._fields_
		)
		return f"{cls.__name__}(\n{fields})"
