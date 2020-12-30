import struct
import zlib
from .crypto.misc import long_to_bytes

def fix_png_size2(f, max_width=10000, max_height=10000):
	f.seek(0x18)
	trailer = f.read(5)  # all the data in IHDR that isn't width or height
	expected = f.read(4)  # crc to match
	for width in range(max_width):
		for height in range(max_height):
			chunk = b"IHDR" + struct.pack(">II", width, height) + trailer
			if long_to_bytes(zlib.crc32(chunk)) == expected:
				f.seek(0x10)
				f.write(struct.pack(">II", width, height))
				return (width, height)
	raise ValueError("Couldn't match CRC32, try using a larger max_width/max_height")

def fix_png_size(filename, max_width=10000, max_height=10000):
	with open(filename, "rb+") as f:
		fix_png_size2(f, max_width, max_height)

def main():
	#pylint: disable=import-outside-toplevel
	import sys
	print(fix_png_size(sys.argv[1]))

if __name__ == "__main__":
	main()
