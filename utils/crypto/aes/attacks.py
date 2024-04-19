import base64
import itertools

from utils.crypto.padding import unpad_pkcs7
from utils.crypto.xor import decrypt_repeating_key_xor, xor
from utils.itertools2 import grouper
from utils.num.misc import round_to_multiple

from .aes import aes_cbc
from .misc import detect_blocksize, detect_ecb


def decrypt_ecb_suffix(oracle):
	# see cryptopals #12/#14
	block_size: int = detect_blocksize(oracle)
	if not detect_ecb(oracle):
		raise ValueError("oracle not using ecb")
	# get prefix length
	common_prefix = None
	prefix_len = None
	for i in range(block_size):
		padding = b"A" * (i + 2 * block_size)
		blocks = list(grouper(oracle(padding), block_size))
		for j, b1, b2 in zip(itertools.count(), blocks, blocks[1:]):
			if b1 == b2:
				common_prefix = padding
				prefix_len = (j + 2) * block_size
				break
		else:
			continue
		break
	if common_prefix is None:
		raise ValueError("Couldn't find prefix length")
	assert prefix_len is not None
	length = round_to_multiple(len(oracle(common_prefix)) - prefix_len, block_size)
	known = bytearray()
	for j in range(length):
		prefix = common_prefix + b"A" * (length - j - 1)
		encrypted = oracle(prefix)[: length + prefix_len]

		for c in range(256):
			encrypted2 = oracle(prefix + known + bytes((c,)))[: length + prefix_len]
			if encrypted == encrypted2:
				known.append(c)
				break
	return bytes(known)


# var names from https://robertheaton.com/2013/07/29/padding-oracle-attack/
# sometimes messes up on the last block in case it accidentally gets the correct padding
def decrypt_cbc_padding_oracle(padding_oracle, ct, iv=None):
	blocks = list(map(bytes, grouper(ct, 16)))
	if iv is not None:
		blocks.insert(0, iv)
	pt_blocks = []
	for c1, c2 in zip(blocks, blocks[1:]):
		pt_block = bytearray()  # reversed
		intermediate_block = bytearray()  # reversed
		for i in range(1, 17):
			for c in range(256):
				c1_ = (
					c1[:-i]
					+ bytes([c])
					+ xor(itertools.repeat(i), reversed(intermediate_block))
				)
				if padding_oracle(c2, c1_):
					intermediate_byte = c ^ i
					pt_byte = c1[-i] ^ intermediate_byte
					pt_block.append(pt_byte)
					intermediate_block.append(intermediate_byte)
					break
		pt_blocks.append(bytes(reversed(pt_block)))
	return unpad_pkcs7(b"".join(pt_blocks))


def decrypt_fixed_nonce_ctr(strs):
	# see cryptopals #20
	blocks_lists = [grouper(s, 16, fillvalue=0) for s in strs]
	transposed_blocks = zip(*blocks_lists)
	plaintexts = [b"" for _ in range(len(strs))]
	for blocks in transposed_blocks:
		plaintext, _ = decrypt_repeating_key_xor(
			b"".join(map(bytes, blocks)), min_len=16, max_len=16, keysizes_to_try=1
		)
		# chunksize isn't 16 to account for non-16 length on last blocks
		plaintext_parts = grouper(plaintext, len(plaintext) // len(strs))
		for i, part in enumerate(plaintext_parts):
			plaintexts[i] += bytes(part)
	return plaintexts


def extract_cbc_iv(s, oracle):
	# see https://github.com/ashutosh1206/Crypton/tree/master/Block-Cipher/CBC-IV-Detection
	# or cryptopals 27
	modified = s[:16] + b"\x00" * 16 + s[:16]
	plaintext = oracle(modified)
	return xor(plaintext[:16], plaintext[-16:])


# partially based on https://github.com/PowerShellMafia/PowerSploit/blob/master/Exfiltration/Get-GPPPassword.ps1
# key from https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-gppref/2c15cbf0-f086-4c74-8b70-1f2fa45dd4be
def decrypt_active_dir_gpo(s):
	return unpad_pkcs7(
		aes_cbc(
			base64.b64decode(s),
			(
				b"\x4e\x99\x06\xe8\xfc\xb6\x6c\xc9\xfa\xf4\x93\x10\x62\x0f\xfe\xe8"
				b"\xf4\x96\xe8\x06\xcc\x05\x79\x90\x20\x9b\x09\xa4\x33\xb6\x6c\x1b"
			),
			b"\x00" * 16,
			"decrypt",
		)
	).decode("utf-16le")
