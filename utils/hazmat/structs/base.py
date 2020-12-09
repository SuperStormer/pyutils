import ctypes

class Struct(ctypes.Structure):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(f"{field[0]}={getattr(self, field[0])}" for field in cls._fields_)
		return f"{cls.__name__}(\n{fields})"
	
	def get_vla(self, field, typ, size):
		return (typ * size).from_address(ctypes.addressof(self) + getattr(type(self), field).offset)
	
	@classmethod
	def from_object(cls, obj):
		""" converts from python object to a struct"""
		return cls.from_address(id(obj))
	
	def to_object(self):
		""" converts struct to python object """
		return ctypes.cast(ctypes.byref(self), ctypes.py_object).value

class Union(ctypes.Union):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(f"{field[0]}={getattr(self, field[0])}" for field in cls._fields_)
		return f"{cls.__name__}(\n{fields})"
