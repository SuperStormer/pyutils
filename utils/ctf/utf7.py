import base64
import string

# https://blog.arkark.dev/2022/11/18/seccon-en/#misc-latexipy
def utf7_encode(s, safe_charset=None):
	if safe_charset is None:
		safe_charset = string.ascii_letters + string.digits + "'(),-./:?"

	out = []
	for c in s:
		if c in safe_charset:
			out.append(c.encode("ascii"))
		else:
			out.append(b"+" + base64.b64encode(c.encode("utf-16be")).rstrip(b"=") + b"-")
	return b"".join(out)
