#!/usr/bin/env python3
import asyncio
import argparse
import atexit
import string
import sys
from pathlib import Path
from sys import call_tracing
from utils.ctftools import pin, INSCOUNT32, INSCOUNT64

def get_args():
	
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-d",
		"--detect",
		action='store_true',
		default=False,
		help='Detect the password length. For example -d -l 40, with 40 characters'
	)
	parser.add_argument('-l', dest='len', type=int, default=10, help='Length of password')
	parser.add_argument(
		'-c',
		"--charset",
		dest='number',
		default="0",
		help=(
		"Charset definition for brute force"
		" (0-Default, 1-Lowercase, 2-Uppercase, 3-Numbers, 4-Hexadecimal, 5-Punctuation, 6-Printable)"
		)
	)
	parser.add_argument(
		'-b', "--character", default='', help='Add characters for the charset. For example, -b _-'
	)
	parser.add_argument(
		'-a', "--arch", default='64', help='Program architecture', choices=["32", "64"]
	)
	parser.add_argument(
		'-i', "--initpass", default='', help='Initial password characters. For example, -i CTF{'
	)
	parser.add_argument('-s', "--symbol", default='-', help='Symbol used as password placeholder')
	parser.add_argument(
		'-e',
		"--expression",
		default='!= 0',
		help=(
		"Difference between instructions that are successful or not."
		" For example: -e '== -12', -e '=> 900', -e '<= 17' or -e '!= 32'"
		)
	)
	parser.add_argument(
		'-r',
		dest='reverse',
		action='store_true',
		default=False,
		help='Reverse order, bruteforcing starting from the last character'
	)
	parser.add_argument(
		'-g',
		"--argv",
		dest='argv',
		action='store_true',
		default=False,
		help='Pass argument via command-line arguments instead of stdin.'
	)
	parser.add_argument('filename', type=Path, help='Program for playing with Pin Tool')
	
	if len(sys.argv) < 2:
		parser.print_help()
		sys.exit()
	
	return parser.parse_args()

def get_charset(charset_num, addchar):
	charsets = {
		'0':
		string.ascii_lowercase + "_{}" + string.digits + string.ascii_uppercase +
		string.punctuation.translate(str.maketrans("", "", "_{}")),
		'1':
		string.ascii_lowercase,
		'2':
		string.ascii_uppercase,
		'3':
		string.digits,
		'4':
		string.hexdigits,
		'5':
		string.punctuation,
		'6':
		string.printable
	}
	
	return "".join(charsets[n] for n in charset_num.split(",")) + ''.join(addchar)

async def detect_length(filename, inscount_file, max_len, symbol="-", argv=False):
	initial = None
	for i in range(1, max_len + 1):
		password = symbol * i
		inscount = await pin(filename, inscount_file, password, argv)
		
		if initial is None:
			initial = inscount
		
		print(
			"%s = with %d characters difference %d instructions" %
			(password, i, inscount - initial)
		)

def add_char(initpass, char, reverse=False):
	
	if reverse:
		initpass = char + initpass
	else:
		initpass += char
	
	return initpass

def get_password(tempassword, char, i, reverse):
	if reverse:
		return tempassword[:i - 1] + char + tempassword[i:]
	else:
		return tempassword[:i] + char + tempassword[i + 1:]

async def solve(
	filename,
	inscount_file,
	passlen,
	charset,
	expression,
	symbfill="-",
	initpass="",
	reverse=False,
	argv=False
):
	password = None
	initlen = len(initpass)
	comparison, number = expression.split(" ")
	number = int(number)
	try:
		cmp_func = {
			"!=": lambda diff: diff != number,
			"<=": lambda diff: diff <= number,
			">=": lambda diff: diff >= number,
			"=>": lambda diff: diff >= number,
			"==": lambda diff: diff == number
		}[comparison]
	except KeyError:
		print("Unknown value for -d option")
		sys.exit(1)
	semaphore = asyncio.Semaphore(5)  #rate limit
	
	async def helper(initial, val, char):
		async with semaphore:
			inscount = await pin(filename, inscount_file, val, argv, f"inscount{char}.out")
			diff = inscount - initial
			print("%s = %d difference %d instructions" % (val, inscount, diff))
			return cmp_func(diff), char
	
	for i in range(initlen, passlen):
		
		if reverse:
			tempassword = symbfill * (passlen - i) + initpass
		else:
			tempassword = initpass + symbfill * (passlen - i)
		
		if reverse:
			i = passlen - i
		#get initial
		char = charset[0]
		initial = await pin(
			filename, inscount_file, get_password(tempassword, char, i, reverse), argv
		)
		
		coros = [
			asyncio.create_task(helper(initial, get_password(tempassword, char, i, reverse), char))
			for char in charset
		]
		for coro in asyncio.as_completed(coros):
			success, char = await coro
			if success:
				for coro in coros:
					coro.cancel()
				initpass = add_char(initpass, char, reverse)
				password = get_password(tempassword, char, i, reverse)
				print(password)
				break
		else:
			print("Password not found, try to change charset...")
			sys.exit(1)
	
	return password

def cleanup():
	for path in Path(".").glob("inscount*.out"):
		path.unlink()
	path = Path("pin.log")
	if path.exists():
		path.unlink()

if __name__ == '__main__':
	
	args = get_args()
	
	initpass = args.initpass
	passlen = args.len
	symbfill = args.symbol
	charset = symbfill + get_charset(args.number, args.character)
	arch = args.arch
	expression = args.expression.strip()
	detect = args.detect
	argv = args.argv
	filename = args.filename.resolve()
	if not filename.exists():
		print("File does not exist.")
		sys.exit(1)
	filename = str(filename)
	if len(initpass) >= passlen:
		print("The length of init password must be less than password length.")
		sys.exit(1)
	
	if passlen > 64:
		print("The password must be less than 64 characters.")
		sys.exit(1)
	
	if len(symbfill) > 1:
		print("Only one symbol is allowed.")
		sys.exit(1)
	
	if arch == "32":
		inscount_file = INSCOUNT32
	elif arch == "64":
		inscount_file = INSCOUNT64
	else:
		print("Unknown architecture")
		sys.exit(1)
	
	atexit.register(cleanup)
	
	if detect is True:
		asyncio.run(detect_length(filename, inscount_file, passlen, symbfill, argv))
		sys.exit()
	password = asyncio.run(
		solve(
		filename, inscount_file, passlen, charset, expression, symbfill, initpass, args.reverse,
		argv
		)
	)
	print("Password: ", password)