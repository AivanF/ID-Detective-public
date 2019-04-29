import json, time
from utils import *

hosts = read_config()

class WorkerHost(object):
	def __init__(self, name):
		self.data = hosts[name]
		self.con = PrettySSH(show_cmd=0, show_out=0, show_basic=False, **self.data['access'])
		print('\tConnected to {}'.format(name))

	def get_workers(self):
		return self.con.execute_parse("ps aux | grep 'worker\\.py' | awk '{print $2}'")

	def show_workers(self, ids=None):
		if ids is None:
			ids = self.get_workers()
		if len(ids) > 0:
			print('{} workers are running: {}'.format(len(ids), ids))
		else:
			print('0 workers are running.'.format(len(ids)))

	def stop_workers(self):
		ids = self.get_workers()
		self.show_workers(ids)
		if len(ids) > 0:
			for el in ids:
				self.con.execute_parse('kill {}'.format(el))
			self.con.say_neutral('Killed them.')

	def __start_worker(self, name):
		cmd = 'cd /aivanf/ID-det/ ; nohup python3 worker.py {0} > worker-{0}.out 2>&1'.format(name)
		temp = PrettySSH(show_basic=False, show_cmd=True, limit_sec=10, timeout=7, **self.data['access'])
		temp.execute_forget(cmd)
		time.sleep(0.1)
		# for part in temp.execute_loop(cmd):
			# print(part)

	def start_workers(self):
		workers = self.data['workers']
		for name in workers:
			self.__start_worker(name)
		time.sleep(1)
		self.con.say_neutral('Started workers!')
		self.show_workers()

	def start_worker(self, name):
		self.show_workers()
		workers = self.data['workers']
		if name in workers:
			self.__start_worker(name)
			self.show_workers()
		else:
			print('Worker {} was not found! Available ones: {}'.format(name, workers))

	def restart_workers(self):
		self.stop_workers()
		self.start_workers()


wh = WorkerHost('fcom')
# wh = WorkerHost('det2')
# wh = WorkerHost('detm')

# wh.show_workers()
wh.stop_workers()
# wh.start_workers()
# wh.restart_workers()

# wh.start_worker('det2-4')
# wh.start_worker('detm-10')
# wh.start_worker('fcom-2')

# for name in hosts:
# 	wh = WorkerHost(name)
# 	wh.show_workers()
	# wh.restart_workers()

