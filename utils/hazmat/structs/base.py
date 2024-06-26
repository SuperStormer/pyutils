import ctypes


class Struct(ctypes.Structure):
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


class Union(ctypes.Union):
	def __repr__(self):
		cls = type(self)
		fields = ",\n".join(
			f"{field[0]}={getattr(self, field[0])}" for field in cls._fields_
		)
		return f"{cls.__name__}(\n{fields})"
