#!/usr/bin/env python3
# based on https://ctftime.org/writeup/21148
import string
import struct

from .keycodes import key_codes

# FORMAT represents the format used by linux kernel input event struct
# See https://github.com/torvalds/linux/blob/v5.5-rc5/include/uapi/linux/input.h#L28
# Stands for: long int, long int, unsigned short, unsigned short, unsigned int

FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(FORMAT)

# keyboard layouts are dicts that map keynames to (normal,shift,alt gr) chars
keyboard_layout_qwerty = {
	**dict(
		zip(string.ascii_uppercase, zip(string.ascii_lowercase, string.ascii_uppercase))
	),
	**dict(zip(string.digits, zip(string.digits, ")!@#$%^&*("))),
	"MINUS": ("-", "_"),
	"EQUAL": ("=", "+"),
	"LEFTBRACE": ("{", "["),
	"RIGHTBRACE": ("}", "]"),
	"SEMICOLON": (";", ":"),
	"APOSTROPHE": ("'", '"'),
	"GRAVE": ("`", "~"),
	"BACKSLASH": ("\\", "|"),
	"COMMA": (",", "<"),
	"DOT": (".", ">"),
	"SLASH": ("/", "?"),
}
keyboard_layout_azerty = {
	**dict(
		zip(string.ascii_uppercase, zip(string.ascii_lowercase, string.ascii_uppercase))
	),
	**dict(zip(string.digits, zip("à&é\"'(-è_ç", string.digits, "@ ~#{[|`\\^"))),
	"Q": ("a", "A"),
	"W": ("z", "Z"),
	"A": ("q", "Q"),
	"Z": ("w", "W"),
	"E": ("e", "E", "€"),
	"1": ("&", "1"),  # no alt gr mapping
	"MINUS": (")", "°", "]"),
	"EQUAL": ("=", "+", "}"),
	"LEFTBRACE": ("^", "¨"),
	"RIGHTBRACE": ("$", "£", "¤"),
	"SEMICOLON": ("m", "M"),
	"APOSTROPHE": ("ù", "%"),
	"BACKSLASH": ("*", "µ"),
	"GRAVE": ("²", ""),
	"M": (",", "?"),
	"COMMA": (";", "."),
	"DOT": (":", "/"),
	"SLASH": ("!", "§"),
	"102ND": ("<", ">"),
}
num_pad_map = {
	"ENTER": "\n",
	"SLASH": "\\",
	"ASTERISK": "*",
	"MINUS": "-",
	"PLUS": "+",
	"DOT": ".",
}


def parse_devinput(in_file, keyboard_layout=None):
	if keyboard_layout is None:
		keyboard_layout = keyboard_layout_qwerty
	out = []
	mode = 0
	for event in iter(lambda: in_file.read(EVENT_SIZE), b""):  # noqa: PLR1702
		(tv_sec, tv_usec, type_, code, value) = struct.unpack(FORMAT, event)  # noqa: F841

		if type_ != 0 or code != 0 or value != 0:
			# print(f"{tv_sec}.{tv_usec}, {type}, {code}, {value}, {value:08b}")

			if type_ == 0x01:  # EV_KEY
				key = key_codes[code][4:]
				if value == 1:  # press key
					if mode == 0:  # normal
						if key in keyboard_layout:
							out.append(keyboard_layout[key][0])
						elif key == "SPACE":
							out.append(" ")
						elif key == "TAB":
							out.append("\t")
						elif key == "ENTER":
							out.append("\n")
						elif key == "BACKSPACE":
							out.append("\b")
						elif key.startswith("KP"):  # num pad
							key = key[2:]
							if key[2:] in string.digits:
								out.append(key)
							elif key in num_pad_map:
								out.append(num_pad_map[key])
							else:
								out.append("KP" + key)
						elif "SHIFT" in key:
							mode = 1
						elif key == "RIGHTALT":
							mode = 2
						else:
							out.append(key)
					elif mode == 1:  # shift
						if key in keyboard_layout:
							out.append(keyboard_layout[key][1])
						else:
							out.append("SHIFT" + key)
					elif mode == 2:  # alt gr
						if key in keyboard_layout and len(keyboard_layout[key]) > 2:
							out.append(keyboard_layout[key][2])
						else:
							out.append("RIGHTALT" + key)
				elif value == 0:  # release key
					if "SHIFT" in key or key == "RIGHTALT":
						mode = 0
	return "".join(out)


def main():
	import argparse  # noqa: PLC0415

	parser = argparse.ArgumentParser()
	parser.add_argument("file", type=argparse.FileType("rb"))
	parser.add_argument("output", type=argparse.FileType("w"), nargs="?", default="-")
	parser.add_argument("--layout", "-l", choices=["azerty", "qwerty"], default="qwerty")
	args = parser.parse_args()
	if args.layout == "qwerty":
		layout = keyboard_layout_qwerty
	elif args.layout == "azerty":
		layout = keyboard_layout_azerty
	else:
		raise ValueError("Invalid layout - this should be impossible")
	print(parse_devinput(args.file, layout), file=args.output)


if __name__ == "__main__":
	main()
