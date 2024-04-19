"""for weird challs like NahamCon CTF 2020 B'omarr Style"""

import base64
import hashlib
import hmac
import json
import math


def non_json_jwt_encode(s: bytes, key, extra_headers=None):
	header_dict = {"alg": "HS256", "typ": "JWT"}
	if extra_headers is not None:
		header_dict.update(extra_headers)
	header = jwt_b64encode(json.dumps(header_dict).encode("utf-8"))
	payload = jwt_b64encode(s)

	signature = jwt_b64encode(
		hmac.new(key, header + b"." + payload, digestmod=hashlib.sha256).digest()
	)
	return b".".join((header, payload, signature))


def non_json_jwt_decode(token: bytes):
	header, token, _ = map(jwt_b64decode, token.split(b"."))
	return json.loads(header), token


def jwt_b64decode(s: bytes):
	padded_len = math.ceil(len(s) / 4) * 4
	return base64.urlsafe_b64decode(s.ljust(padded_len, b"="))


def jwt_b64encode(s: bytes):
	return base64.urlsafe_b64encode(s).rstrip(b"=")
