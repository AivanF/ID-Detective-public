from threading import Lock
import json, time
from os.path import join, isfile
from flask import Flask, request

from utils import *
from faces import read_files, find_faces
from dbvk import DBVk, MAX_NAME_LEN

EXPIRE_DAYS = 1
TASK_SIZE = 1000
WELL = set([1, 'true', '1', 'yes', 'True', 't', 'T'])
FL_TIMES = 'times-server-vk.json'

MUST_WORK = True
# MUST_WORK = False
activities_ = {}
timesmutex = Lock()


def time_log(worker, seconds, count, notes):
	if seconds > 4 * 60 or count < 3:
		return
	times = {}
	if count % 10 == 9:
		count += 1
	timesmutex.acquire()
	if isfile(FL_TIMES):
		times.update(read_json(FL_TIMES))
	if worker in times:
		times[worker]['seconds'] += seconds
		times[worker]['count'] += count
	else:
		times[worker] = {
			'seconds': seconds,
			'count': count,
		}
	if notes is not None:
		if 'notes' not in times[worker]:
			times[worker]['notes'] = {}
		dsum(times[worker]['notes'], notes)
	save_json(FL_TIMES, times)
	timesmutex.release()


def time_report():
	if isfile(FL_TIMES):
		res = read_json(FL_TIMES)
		notes = {}
		total_seconds = 0
		total_count = 0
		total_speed = 0
		for worker in res:
			cur = res[worker]
			if 'notes' in cur:
				dsum(notes, cur['notes'])
			seconds = cur['seconds']
			count = cur['count']
			antispeed = seconds / count
			# res[worker]['People/Sec'] = antispeed
			res[worker] = '{} IDs, {:.2f} hours, {:.2f} sec/acc'.format(
				count, seconds/3600, antispeed)
			total_seconds += seconds
			total_count += count
			total_speed += count / seconds
		res['__'] = '{} IDs, {:.2f} hours, AVG: {:.2f} sec/acc, TOTAL: {:.2f} sec/acc'.format(total_count, total_seconds/3600, total_seconds/total_count, 1/total_speed)
		return res, notes
	else:
		return {}, {}


app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello_world():
	global MUST_WORK
	# db = DBVk()
	# db.create_function()
	# return 'Function recreated!'

	# print(request.headers)
	# print(request.args)
	# json_data = request.get_json(force=True)
	res = 'Hello World!'
	if 'work' in request.args:
		MUST_WORK = request.args['work'] in WELL
		res = 'MUST_WORK = {}'.format(MUST_WORK)
	# res = debugit(request.remote_addr, 'Your IP')
	return res
	# biny = request.data
	# biny = biny.split(b'.')
	# return b'You wrote: ' + biny[1]


@app.route('/Vk/Stats', methods=['GET'])
def vk_stats():
	db = DBVk()
	data = db.get_stats()
	res = '<h3>Stats:</h3>'
	for key in data:
		res += '- {}: {}<br>\n'.format(key, data[key])
	res += '<br>\n<br>\n<h3>MUST_WORK: {}</h3>'.format(MUST_WORK)
	return res


@app.route('/Vk/Tasks', methods=['GET'])
def vk_tasks():
	db = DBVk()
	data = db.select_tasks_opened()
	res = '<h3>Opened tasks:</h3>'
	for row in data:
		res += str(row) + '<br>\n'

	res += '<br>\n<h3>Last seen:</h3>' 
	now = int(time.time())
	for worker, cur in sorted(activities_.items(), key=lambda x: x[0]): 
		dif = now - cur
		if dif < 60 * 4:
			res += '- {}: {}'.format(worker, dif)
		elif dif < 60 * 60 * 24:
			res += '- {}: long time ago'.format(worker)
		else:
			res += '- {}: very long time ago'.format(worker)
		res += '<br>\n'

	times, notes = time_report()

	res += '<br>\n<h3>Part time:</h3>'
	for worker, cur in sorted(times.items(), key=lambda x: x[0]): 
		if worker[0] == '_':
			res += '{}<br><br>\n'.format(cur)
		else:
			res += '{}: {}<br>\n'.format(worker, cur)
	
	res += '<br>\n<h3>Events:</h3>'
	for key, cnt in sorted(notes.items(), key=lambda x: x[0]): 
		res += '{}: {}<br>\n'.format(key, cnt)

	res += '<br>\n<h3>MUST_WORK: {}</h3>'.format(MUST_WORK)
	res += '<br>\n<a href="/?work=1" target="_blank">Enable</a> '
	res += '/ <a href="/?work=0" target="_blank">Disable</a>'
	return res


def get_ip():
	ip = request.remote_addr
	if isinstance(ip, str) and len(ip.split('.')) == 4:
		return ip
	else:
		return '0.0.0.0'


@app.route('/Vk/GetTask/', methods=['GET'])
def get_task():
	if not MUST_WORK:
		return '{"sleep":1}'
	worker = request.values['name']
	ip = get_ip()
	db = DBVk()
	res = db.select_task_debt(worker)
	if res is not None:
		expire = db.update_task(res['id'], worker, ip, res['down'], res['up'], days=EXPIRE_DAYS)
		res['expire'] = expire
		res['comment'] = 'Your debt'
	else:
		res = db.select_task_free()
		if res is not None:
			expire = db.update_task(res['id'], worker, ip, res['down'], res['up'], days=EXPIRE_DAYS)
			res['expire'] = expire
			res['comment'] = 'Someone`s debt'
		else:
			ind, down = db.select_task_new()
			up = down - 1 + TASK_SIZE
			expire = db.insert_task(ind, worker, ip, down, up, days=EXPIRE_DAYS)
			res = {
				'id': ind,
				'worker': worker,
				'ip': ip,
				'down': down,
				'up': up,
				'expire': expire,
			}
			res['comment'] = 'New task'
	log_inf('GetTask: {}@{} got task ID {} as {}'.format(worker, ip, res['id'], res['comment']))
	db.commit_db()
	return json.dumps(res)


SUBMIT_CODES = {
	0: 'Deactivate',
	1: 'Data was loaded, you can delete the file',
	2: 'Try to load the file later',
	3: 'The file is bad, delete it',
}

@app.route('/Vk/SubmitTask/', methods=['POST'])
def submit_task():
	res = {}
	comment = ''

	if not MUST_WORK:
		code = 0
	else:
		code = 2
		# code = 3
		if len(request.files) == 0:
			comment = 'file not found'
		elif len(request.files) > 1:
			comment = 'too many files'
		else:
			file = None
			for key in request.files:
				file = request.files[key]
				break
			data = None
			try:
				data = load_pickle(file)
			except:
				pass
			try:
				if data is not None and isinstance(data, dict) and 'vk_task_id' in data:
					ip = get_ip()
					worker = request.form['name']
					ind = data['vk_task_id']
					down = int(data['vk_from'])
					up = int(data['vk_to'])
					label = 'Task {} from {} to {}'.format(ind, down, up)
					label += ' Rows: {}'.format(len(data['data']))
					res['file'] = label

					db = DBVk()
					can_load = False
					meta = db.select_task_id(ind)
					if meta is None:
						comment = 'task was not found'
					else:
						if meta['up'] == meta['down']:
							comment = 'task is already completed'
							code = 3
						elif meta['worker'] != worker:
							comment = 'different name'
							log_er('SubmitTask: {}@{} tries to submit task of {}, ID is {}'.format(worker, ip, meta['worker'], ind))
						elif down - meta['down'] < 3:
							can_load = True
						else:
							comment = 'need user_id since {}, not {}'.format(meta['down'], down)
					if can_load:
						for row in data['data']:
							# print('\n- Row:')
							# print(row)
							db.insert_features(row[0], row[1], row[2])
						new_down = min(up, meta['up'])
						db.update_task(ind, worker, ip, new_down, meta['up'], days=EXPIRE_DAYS)
						db.commit_db()
						code = 1
						comment = 'very well ' + str(len(data['data']))
						log_inf('SubmitTask: {}@{} loaded task ID {} from {} to {}'.format(worker, ip, ind, down, up))

						now = int(time.time())
						if worker in activities_:
							time_log(worker, now - activities_[worker], up-down, data.get('notes'))
						activities_[worker] = now
					else:
						log_inf('SubmitTask: {}@{} cannot load task ID {} from {} to {} because "{}"'.format(
							worker, ip, ind, down, up, comment))
			except Exception as ex:
				log_ex(ex, label, show=1)
				comment = 'very bad file'

	res['code'] = code
	res['descr'] = SUBMIT_CODES.get(code, '?')
	res['comment'] = comment
	# print(res)
	return json.dumps(res)


def get_request_face():
	file = None
	face = None
	comment = ''
	if len(request.files) == 0:
		comment = 'File not found'
	elif len(request.files) > 1:
		comment = 'Too many files'
	else:
		for key in request.files:
			file = request.files[key]
			break
		faces = find_faces(read_files(file))
		if len(faces) == 0:
			comment = 'Faces not found!'
		else:
			if len(faces) > 1:
				comment = 'Warning: file has multiple faces! Random one will be used.'
			face = faces[0]
	return face, comment


@app.route('/Vk/FindPerson/', methods=['GET', 'POST'])
def find_person():
	# TODO: remove WHERE from this method
	res = {}
	done = False
	bits_threshold = int(request.form['bits_threshold']) if 'bits_threshold' in request.form else None
	where = request.form['where'] if 'where' in request.form else ''
	face, comment = get_request_face()
	if face is not None:
		db = DBVk()
		res['found'] = db.select_matches(face, bits_threshold=bits_threshold, where=where)
		done = True
	res['done'] = done
	res['comment'] = comment
	return json.dumps(res)


@app.route('/Vk/CompareFace/', methods=['GET', 'POST'])
def compares_face():
	res = {}
	done = False
	user_id = request.form['user_id']
	face, comment = get_request_face()
	if face is not None:
		db = DBVk()
		res['found'] = db.select_compare(face, user_id)
		done = True
	res['done'] = done
	res['comment'] = comment
	return json.dumps(res)


@app.route('/Vk/FindThreshold/', methods=['GET', 'POST'])
def find_threshold():
	res = {}
	done = False
	comment = ''
	limit_first = int(request.form['limit_first'])
	limit_second = int(request.form['limit_second'])
	where = request.form['where'] if 'where' in request.form else ''
	face, comment = get_request_face()
	if face is not None:
		db = DBVk()
		res['found'] = db.select_threshold(values=face, limit_first=limit_first, limit_second=limit_second, where=where)
		done = True
	res['done'] = done
	res['comment'] = comment
	return json.dumps(res, default=str)
	

if __name__ == '__main__':
	setup_logger('-server-db')
	# host = '127.0.0.1'
	host = '0.0.0.0'
	app.run(host, 5151, debug=False)

