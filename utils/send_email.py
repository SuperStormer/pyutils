#!/usr/bin/env python3
import smtplib
import ssl
import sys
from email.message import EmailMessage
from typing import Tuple, Union

def send_email(
	sender_email: str,
	receiver_emails: Union[Tuple[str, ...], str],
	password: str,
	subject: str,
	content: str,
	*,
	from_email: str = None,
	smtp_server: str = "smtp.gmail.com"
):
	if from_email is None:
		from_email = '""'
	port = 465  # For SSL
	message = EmailMessage()
	message.set_content(content)
	message["Subject"] = subject
	message["From"] = from_email
	message["To"] = receiver_emails
	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)
		server.send_message(message)

if __name__ == "__main__":
	sender_email = input("Sender?").strip()
	receiver_emails = tuple(map(str.strip, input("Receipents?").split(",")))
	password = input("Password?").strip()
	subject = input("Subject?").strip()
	print("Content?")
	content = "\n".join(sys.stdin.readlines())
	send_email(sender_email, receiver_emails, password, subject, content)
