import json, time
from utils import *

# server_name = 'fcom'
server_name = 'detm'

hosts = read_config()
access = hosts[server_name]['access']
con = PrettySSH(show_cmd=0, show_out=0, **access)


def get_server():
	return con.execute_parse("ps aux | grep 'server\\.py' | awk '{print $2}'")
	# This does not work in old shell after server starting
	# return con.execute_parse("lsof -t -i:5151")


def start_server():
	temp = PrettySSH(show_basic=False, show_cmd=True, limit_sec=10, timeout=7, **access)
	temp.execute_forget("cd /aivanf/ID-det/ ; nohup python3 server.py > server.out 2>&1")
	time.sleep(1)
	print(get_server())


def stop_server():
	ids = get_server()
	if len(ids) > 0:
		for el in ids:
			con.execute_parse('kill {}'.format(el))
		print('Killed {} processes'.format(len(ids)))


def restart_server():
	stop_server()
	start_server()


print(get_server())
# stop_server()
# start_server()
restart_server()

