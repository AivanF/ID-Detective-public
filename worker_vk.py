import os
from os.path import basename, join
import datetime, time
import requests, json
import numpy as np

from utils import *
from handler import load_person, load_people
from vk import VkAccess, f_get_user_photos, f_kwargs_vk
from faces import read_files, find_faces

# Bytes to NumPy array
# https://stackoverflow.com/q/50630045/5308802
# NumPy array from bytes
# https://stackoverflow.com/a/11760170/5308802


@multi_all
def person2dict(user_id, results=None, **kwargs):
	def f_save_face(user_id, name, values, kwargs):
		results.append((user_id, name, values))

	load_person(user_id, **kwargs, f_get_user_photos=f_get_user_photos,
		f_save_face=f_save_face, f_exists_user_id=None, f_commit=None)


TASK_STATUSES = {
	0: 'task is 0k',
	1: 'the worker was not initialised',
	2: 'the range is negative',
	3: 'completed this range',
	4: 'the task is expired',
}

VK_API_ERRORS = ['no access to call', 'invalid session', 'Too many', 'server error']


def check_task_status(commands, b=None):
	if commands['vk_task_id'] < 0:
		return 1
	elif commands['vk_from'] < 0:
		return 2
	elif commands['vk_from'] >= commands['vk_to']:
		return 3
	elif time.time() > commands['vk_expiration']:
		return 4
	else:
		return 0


def process_vk_tasks(commands, params):
	st = check_task_status(commands)
	if st != 0:
		reason = TASK_STATUSES.get(st, '[error]')
		if 'nonew' in params and params['nonew'] == 'nonew':
			commands['must_work'] = False
			print('Completed the task and shutting down')
			return

		log_inf('Requesting Central because: {}'.format(reason), 1)
		url = 'http://' + join(params['center'], 'Vk/GetTask/') + '?name=' + params['name']
		try:
			response = requests.get(url)
			data = response.content.decode('utf-8')
			if response.status_code == 200:
				data = json.loads(data)
				if 'sleep' in data:
					commands['must_work'] = False
					print('Server asked to deactivate.')
				elif 'id' in data:
					commands['vk_task_id'] = data['id']
					commands['vk_from'] = data['down']
					commands['vk_to'] = data['up']
					commands['vk_expiration'] = data['expire']
					commands['dones'] = 0
					if 'comment' in data:
						commands['vk_comment'] = data['comment']
				else:
					log_er('GetTask no id, data:<br>\n{}'.format(data), 1)
			else:
				log_er('GetTask bad code: {}, data:<br>\n{}'.format(response.status_code, data), 1)
		except requests.exceptions.ConnectionError as ex:
			incr(commands, 'Vk/GetTask-error')

	if check_task_status(commands) != 0:
		# incr(commands, 'Vk/GetTask-still-no')
		return

	if params['vk_tokens'] is None or len(params['vk_tokens']) == 0:
		log_er('Vk token is None!', 1)
		return

	# Process subrange, save indices.
	down = commands['vk_from']
	up = commands['vk_to']
	up = min(up, down + params['pack_size'])
	print('Doing task #{} from {} to {}, the goal is {}'.format(commands['vk_task_id'], down, up, commands['vk_to']))
	people = list(range(down, up))
	results = []
	
	pro = Progress(len(people), change=9, key='vk.proc')
	load_people(people, person2dict, pro,
		kwargs={'results':results},
		cyclic_args={'vka':params['vk_tokens']},
		kwargs_processors=[f_kwargs_vk],
		threads_count=params.get('threads_count', None))

	api_errors = dfindsum(pro.notes, VK_API_ERRORS)
	# if len(results) > 0:
	if api_errors < (up-down) / 3:
		log_inf('- Worker Vk: got {} API errors.'.format(api_errors))
		done = {
			'vk_task_id': commands['vk_task_id'],
			'vk_from': down,
			'vk_to': up,
			'data': results,
			'notes': pro.notes
		}
		name = '{} {} {} {}-{}.dat'.format(params['name'], commands['vk_task_id'], str(commands['dones']).zfill(3), down, up)
		path = join(params['done'], name)
		save_pickle(path, done)
		commands['vk_from'] = up
		incr(commands, 'dones')
	else:
		# log_er('- Worker Vk Error: completely no faces extracted! Killing process.'.format())
		log_er('- Worker Vk Error: too many API errors ({})! Killing process. Notes:\n{}'.format(api_errors, pro.notes))
		commands['must_work'] = False


def try_upload(name, path, commands, params):
	data = load_pickle(path)
	if isinstance(data, dict):
		if 'vk_task_id' in data:
			# label = '- Found done file {}:'.format(name)
			# label += '\n{}:{} #{}'.format(data['vk_from'], data['vk_to'], data['vk_task_id'])
			# label += '\nRows: {}'.format(len(data['data']))
			# print(label)

			# Delete if success
			# and update expiration date.
			url = 'http://' + join(params['center'], 'Vk/SubmitTask/')

			files = {name + '.dat': open(path,'rb')}
			values = {'name': params['name']}
			try:
				response = requests.post(url, files=files, data=values)
				data = response.content.decode('utf-8')
				if response.status_code == 200:
					data = json.loads(data)
					if data['code'] == 1:
						os.remove(path)
						print('Loaded file {}'.format(name))
					elif data['code'] == 3:
						# This should never happen
						os.remove(path)
						temp = 'Deleted mal file {}'.format(name)
						log_er(temp)
						print(temp)
					elif data['code'] == 0:
						commands['must_work'] = False
						print('Server asked to deactivate.')
					else:
						print('Got data: {}'.format(data))
					return data['code']
				else:
					log_er('SubmitTask bad code: {}, data:<br>\n{}'.format(response.status_code, data), 1)
					return response.status_code
			except requests.exceptions.ConnectionError as ex:
				incr(commands, 'Vk/SubmitTask-error')
	else:
		return -1
		# data_old = data[0]
		# data_new = np.fromstring(data_old.tobytes())
		# print('Dif:')
		# print(np.subtract(data_new, data_old).sum())
	


def process_vk_submit(commands, params):
	# print('- process_submit:')
	# print(datetime.datetime.now())

	completed = find_filenames(params['done'], '.dat')
	if len(completed) == 0:
		return
	names = list(completed.keys())
	names.sort()
	for name in names:
		if name.split(' ')[0] == params['name']:
			try_upload(name, completed[name], commands, params)

