import asyncio
import contextlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from mimetypes import guess_all_extensions

import aiofiles
import aiohttp
from bs4 import BeautifulSoup, SoupStrainer

URL = "https://www.google.com/search?q={}&source=lnms&tbm=isch"
HEADERS = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
}
VALID_IMAGE_EXTENSIONS = {"jpg", "png", "jpeg", "gif"}


class InvalidExtensionError(Exception):
	pass


def _parse_image_html(text, limit=15):
	only_image_info = SoupStrainer("div")
	soup = BeautifulSoup(text, "lxml", parse_only=only_image_info)
	return tuple(
		json.loads(str(info.string))["ou"]
		for info in soup.find_all(class_="rg_meta", limit=limit)
	)


async def get_urls(keyword, limit=15, session=None, executor=None):
	async with contextlib.AsyncExitStack() as stack:
		if session is None:
			session = await stack.enter_async_context(aiohttp.ClientSession())
		if executor is None:
			executor = stack.enter_context(ProcessPoolExecutor(max_workers=1))
		async with session.get(
			URL, params={"q": keyword, "source": "lnms", "tbm": "isch"}, headers=HEADERS
		) as response:
			loop = asyncio.get_event_loop()
			# return _parse_image_html(await response.text(), limit)
			return await loop.run_in_executor(
				executor, _parse_image_html, await response.text(), limit
			)


async def _download_helper(path, url, session):
	async with session.get(url) as response:
		# from https://stackoverflow.com/q/29674905/7941251
		content_type = response.headers["content-type"].partition(";")[0].strip()
		if content_type.partition("/")[0] == "image":
			try:
				ext = (
					"."
					+ (
						{
							ext[1:] for ext in guess_all_extensions(content_type)
						}.intersection(VALID_IMAGE_EXTENSIONS)
					).pop()
				)
			except KeyError:
				raise InvalidExtensionError(
					f"No valid extensions found. Extensions: {guess_all_extensions(content_type)}"
				) from None

		else:
			raise InvalidExtensionError("No extensions found.")

		filename = f"{path}{ext}"
		# from https://stackoverflow.com/q/38358521/7941251
		async with aiofiles.open(filename, "wb") as out_file:
			block_size = 1024 * 8
			while True:
				block = await response.content.read(block_size)  # pylint: disable=no-member
				if not block:
					break
				await out_file.write(block)
		return filename


async def download_images(
	directory: str, keyword: str, limit: int = 15, session=None, executor=None
):
	if not os.path.exists(directory):
		os.makedirs(directory)
	async with contextlib.AsyncExitStack() as stack:
		if session is None:
			session = await stack.enter_async_context(aiohttp.ClientSession())
		if executor is None:
			executor = stack.enter_context(ProcessPoolExecutor(max_workers=1))
		urls = await get_urls(keyword, limit, session, executor)
		return await asyncio.gather(
			*(
				_download_helper(f"{directory}/{i}", url, session)
				for i, url in enumerate(urls)
			)
		)


def main():
	import argparse  # noqa: PLC0415

	parser = argparse.ArgumentParser()
	parser.add_argument("keyword")
	parser.add_argument("directory")
	parser.add_argument("--limit", "-l", "-n", type=int, default=15)
	args = parser.parse_args()
	asyncio.run(download_images(args.directory, args.keyword, args.limit))


if __name__ == "__main__":
	main()
