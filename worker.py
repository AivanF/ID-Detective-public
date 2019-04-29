import sys
from os import getcwd
from os.path import isfile, join
import threading, time, json

from utils import *
from worker_vk import process_vk_tasks, process_vk_submit

# The code needs these folders: Configs, State, Log, Done
# os.path.abspath(os.path.join('todo/aivanf/lolka/tasks', os.pardir, 'templates'))

CWD = getcwd()
DIR_DONE = join(CWD, 'Done')
FL_COM = None
SLEEP_MINUTES = 1.0
SLEEP_MINUTES = 0.1
must_work__ = False
config__ = None
firstly__ = True


def commands_load():
	commands = {
		'vk_task_id': -1,
		'vk_from': -1,
		'vk_to': -1,
		'vk_expiration': -1,
		'dones': 0,
	}
	if isfile(FL_COM):
		commands.update(read_json(FL_COM))
	commands['must_work'] = must_work__
	return commands


def process_main():
	global must_work__, firstly__
	commands = commands_load()
	params = {
		'done': DIR_DONE,
		'pack_size': 50,
		'threads_count': 5,
	}
	params.update(config__)
	if firstly__:
		firstly__ = False
		process_vk_submit(commands, params)
	if commands['must_work']:
		process_vk_tasks(commands, params)
	if commands['must_work']:
		process_vk_submit(commands, params)
	save_json(FL_COM, commands)
	if not commands['must_work']:
		must_work__ = False


def cycles(cycle_target, delay):
	next_call = time.time()
	while must_work__:
		cycle_target()
		if not must_work__:
			break
		time.sleep(delay * 60)


def run_periodic(cycle_target, delay):
	the = threading.Thread(target=cycles, kwargs={
		'cycle_target': cycle_target,
		'delay': delay,
	})
	# the.daemon = True
	the.start()
	return the


def find_config():
	files = find_filenames(CWD, '.json')
	for name in files:
		if 'config' in name:
			return name, files[name]
	return None, None


def load_config(filename=None):
	global must_work__, config__
	# filename, path = find_config()

	if filename is not None:
		path = join(CWD, 'Configs/config-{}.json'.format(filename))
		config__ = read_json(path)
	
	if config__ is None:
		print('File config.json was not found!')

	elif all (k in config__ for k in ('vk_tokens', 'name', 'center', 'sleep_minutes')):
		print('ID-Worker-Vk "{}" is starting'.format(config__['name']))
		# set_timer_file(join(CWD, 'Logs/time-{}.txt'.format(config__['name'])))
		must_work__ = True

	else:
		print('Mal config file {}.json'.format(filename))


if __name__ == '__main__':
	args = sys.argv
	if len(args) < 2:
		print('Config file must be specified!')
	else:
		load_config(args[1])
	if must_work__:
		me = SingleInstance(flavor_id=config__['name'])
		setup_logger(config__['name'])
		if 'nonew' in config__ and config__['nonew'] == 'nonew':
			print('\tNo New Mode is ON!')
		FL_COM = join(CWD, 'State/worker-{}.json'.format(config__['name']))
		run_periodic(process_main, config__['sleep_minutes'])
	else:
		print('Cannot work.')

