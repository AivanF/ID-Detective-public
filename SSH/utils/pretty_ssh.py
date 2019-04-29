from pyparsing import *
import paramiko
import time
# import socket

NOT_FOUND = 'not found'


class OutputIterator(object):
	def __init__(self, ssh):
		self.ssh = ssh
		self.completed = False

	def __iter__(self):
		return self

	def __next__(self):
		if self.completed:
			raise StopIteration
		else:
			part = self.ssh.get_part()
			self.completed = self.ssh.check_finish(part)
			return part


class PrettySSH(object):
	"""
	Handy wrapper class for Paramiko SSH shell.
	Works with Ubuntu.
	"""
	def __init__(self,
			host, user, pw, port=None,
			show_basic=True, show_cmd=False, show_out=False,
			limit_sec=180, timeout=120):
		"""
		timeout is max wait time for single line
		limit_sec is max wait time for single command
		"""
		self.user = user
		self.show_cmd = show_cmd
		self.show_out = show_out
		self.show_basic = show_basic
		self.limit_sec = limit_sec

		if port is None:
			port = 22
		self.host = host
		self.s = paramiko.SSHClient()
		self.chan = None
		self.s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.s.connect(host, username=user, password=pw, port=port)
		# starts an interactive session
		self.chan = self.s.invoke_shell()
		self.chan.settimeout(timeout) 

		if self.show_basic:
			self.say_neutral('SSH connected to {}'.format(host))
		self.wait()
		# TODO: extract OS name & version
		self.get_results()

	def __del__(self):
		if self.chan is not None:
			# Stopping aborts nohup from execute_forget
			# self.stop()
			self.chan.close()
			self.s.close()
			if self.show_basic:
				self.say_neutral('SSH is closed')

	def stop(self):
		self.chan.send('\x03')
		self.say_bad('Stop signal')

	def say_good(self, txt):
		print('+\t{}'.format(txt))

	def say_bad(self, txt):
		print('-\t{}'.format(txt))

	def say_neutral(self, txt):
		print('\t{}'.format(txt))

	def wait(self, max_wait=5):
		count = 0
		sleep_time = 0.2
		time.sleep(sleep_time)
		while count < max_wait / sleep_time:
			if self.chan.recv_ready():
				return
			time.sleep(sleep_time)
			count += 1
		raise Exception('Too long delay!')

	def check_finish(self, output):
		return '#' in output[-4:]

	def get_part(self):
		part = self.chan.recv(2048).decode('utf-8')
		if part[-2:] == '\r\n':
			part = part[:-2]
		return part
		# except socket.timeout:

	def get_results(self, split=True, skip_empty=True, show_out=False, limit_sec=None):
		# TODO: add limit_lines
		output = ''
		count = 0
		success = False
		if limit_sec is None:
			limit_sec = self.limit_sec
		begin = time.time()
		# while count < 10000:
		while True:
			count += 1
			if time.time() - begin > limit_sec:
				break
			part = self.get_part()
			output += part + '\n'
			if show_out:
				print(part)
			# Looping until the end
			if self.check_finish(part):
				success = True
				break
			time.sleep(0.1)

		if not success:
			raise Exception('Too long output!\n{}'.format(output))
		if self.show_out and not show_out:
			print(output)

		res = output.replace('\r', '\n')
		if split:
			res = [el for el in res.split('\n') if len(el) > 0]
			# if show_out:
			# 	print('skip_len_0')
			# 	print(res)
			skip_first = True
			if skip_empty:
				marker = self.user + '@'
				if marker in res[0]:
					# Sometimes user@host is sent with the command
					# If so, the command will be already filtered
					# and skip_first will erase precious output.
					if res[0].split('#')[1] > 2:
						# So, we check if the command was sent with user@host
						skip_first = False
						# print('prevent skip_first')
				res = [el for el in res if marker not in el]
				# if show_out:
				# 	print('skip_empty')
				# 	print(res)
			if skip_first:
				res = res[1:]
				# if show_out:
				# 	print('skip_first')
				# 	print(res)
		return res

	def execute_parse(self, cmd, show_cmd=False, **kwargs):
		if show_cmd or self.show_cmd:
			self.say_neutral('Calling "{}"'.format(cmd))
		self.chan.send(cmd + '\r\n')
		self.wait()
		return self.get_results(**kwargs)

	def execute_loop(self, cmd, show_cmd=False):
		# TODO: add limit_sec, limit_lines
		if show_cmd or self.show_cmd:
			self.say_neutral('Calling loop "{}"'.format(cmd))
		self.chan.send(cmd + '\r\n')
		self.wait()
		return OutputIterator(self)

	def execute_forget(self, cmd, show_cmd=False, **kwargs):
		if show_cmd or self.show_cmd:
			self.say_neutral('Calling "{}"'.format(cmd))
		self.chan.send(cmd + '\r\n')

	def exec_ls(self):
		output = self.execute_parse('ls')
		output = ' '.join(output)
		# https://bixense.com/clicolors/
		# https://stackoverflow.com/a/3663767/5308802
		ESC = Literal('\x1b')
		integer = Word(nums)
		escapeSeq = Combine(ESC + '[' + Optional(delimitedList(integer,';')) + oneOf(list(alphas)))
		nonAnsiString = lambda s: Suppress(escapeSeq).transformString(s)
		# TODO: determine folder vs files
		output = nonAnsiString(output)
		res = []
		state = 0
		ind, prev = 0, 0
		for ch in output:
			if state == 1:
				# just name
				if ch == ' ':
					res.append(output[prev:ind])
					state = 0
				pass
			elif state == 2:
				# q mark
				if ch == "'":
					res.append(output[prev:ind])
					state = 0
			else:
				if ch == "'":
					state = 2
					prev = ind + 1
				elif ch != " ":
					state = 1
					prev = ind
			ind += 1
		return res

	def exec_pwd(self):
		output = self.execute_parse('pwd')
		if len(output) > 0:
			return output[0]
		else:
			raise Exception('No output!')

	def exec_cd(self, path):
		output = self.execute_parse('cd ' + path)
		if len(output) > 0:
			if self.show_out:
				print(output[0])
			return False
		else:
			return True

	def exec_rm(self, filename):
		output = self.execute_parse('rm ' + filename)
		if len(output) > 0:
			if self.show_out:
				print(output[0])
			return False
		else:
			return True

	def exec_rmdir(self, path):
		output = self.execute_parse('rmdir ' + apth)
		if len(output) > 0:
			if self.show_out:
				print(output[0])
			return False
		else:
			return True

	def exec_isfound(self, cmd, **kwargs):
		output = self.execute_parse(cmd, **kwargs)
		if len(output) > 0:
			return NOT_FOUND not in output[0]
		else:
			raise Exception('No anwser for "{}"'.format(cmd))
			return False

	def pip_list(self, pip_name='pip', **kwargs):
		output = self.execute_parse('{} list --format=columns'.format(pip_name), **kwargs)[2:]
		res = {}
		for row in output:
			cur = [el.lower().replace('-', '_') for el in row.split(' ') if len(el) > 1]
			if len(cur) != 2:
				continue
			res[cur[0]] = cur[1]
		return res

	def pip_install(self, module, pip_name='pip', **kwargs):
		res = self.execute_parse('{} install {}'.format(pip_name, module), split=False, **kwargs)
		res = res[-300:]
		if 'failed' in res or 'error' in res:
			print(res)
			return False
		else:
			return True

