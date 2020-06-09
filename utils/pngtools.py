import struct
import zlib
from utils.crypto.misc import long_to_bytes

def fix_png_size(filename):
	with open(filename, "rb+") as f:
		f.seek(0x18)
		trailer = f.read(5)  # all the data in IHDR that isn't width or height
		expected = f.read(4)  # crc to match
		for width in range(10000):
			for height in range(10000):
				chunk = b"IHDR" + struct.pack(">II", width, height) + trailer
				if long_to_bytes(zlib.crc32(chunk)) == expected:
					f.seek(0x10)
					f.write(struct.pack(">II", width, height))
					return (width, height)

if __name__ == "__main__":
	import sys
	print(fix_png_size(sys.argv[1]))
