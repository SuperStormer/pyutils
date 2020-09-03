from pathlib import Path
import asyncio
import subprocess
"""used for certain rev challs """

PIN = Path("~/pin/pin").expanduser()
INSCOUNT32 = Path("~/pin/source/tools/ManualExamples/obj-ia32/inscount0.so").expanduser()
INSCOUNT64 = Path("~/pin/source/tools/ManualExamples/obj-intel64/inscount0.so").expanduser()

def pin_sync(filename, inscount, passwd, argv=False, out_file="inscount.out"):
	if argv:
		subprocess.run(
			[PIN, "-t", inscount, "-o", out_file, "--", filename, passwd],
			check=False,
		)
	else:
		subprocess.run(
			[PIN, "-t", inscount, "-o", out_file, "--", filename],
			input=passwd.encode() + b"\n",
			check=False,
		)
	with open(out_file) as f:
		output = f.read()
		return int(output.partition(" ")[2])

async def pin(filename, inscount, val, argv=False, out_file="inscount.out"):
	if argv:
		process = await asyncio.create_subprocess_exec(
			PIN,
			"-t",
			inscount,
			"-o",
			out_file,
			"--",
			filename,
			val,
			stdout=asyncio.subprocess.DEVNULL
		)
		_, _ = await process.communicate()
	else:
		process = await asyncio.create_subprocess_exec(
			PIN,
			"-t",
			inscount,
			"-o",
			out_file,
			"--",
			filename,
			stdin=asyncio.subprocess.PIPE,
			stdout=asyncio.subprocess.DEVNULL
		)
		_, _ = await process.communicate(val.encode() + b"\n")
	with open(out_file) as f:
		output = f.read()
		return int(output.partition(" ")[2])
