# General dependencies:
# dlib, face_recognition, MySQLdb (mysqlclient), flask
import sys
if sys.version_info.major < 3 or sys.version_info.minor < 3:
	raise Exception('Old Python version: ' + sys.version)
from os.path import join
import requests, json

from utils import *
from handler import load_person, load_people
from vk import VkAccess, f_get_user_photos, f_kwargs_vk
from faces import read_files, find_faces, compare_my
from dbvk import MAX_NAME_LEN, DBVk


VK_TOKEN = 'xxxxx'


def person2db(user_id, db=None, **kwargs):
	def f_exists_user_id(user_id, kwargs):
		return db.exists_user_id(user_id)
	def f_save_face(user_id, name, values, kwargs):
		db.insert_features(user_id, name, values)
	def f_commit(kwargs):
		db.commit_db()

	load_person(user_id, **kwargs, f_get_user_photos=f_get_user_photos,
		f_save_face=f_save_face, f_exists_user_id=f_exists_user_id, f_commit=f_commit)


def files2db(db, path):
	count = 0
	tick('files2db')
	filenames = find_filenames(path, ext='.dat')
	tick('files2db', '1_read_files')
	for key in filenames:
		parts = key.split('-')
		if len(parts) == 2:
			faces = load_pickle(filenames[key])
			user_id = int(parts[0])
			name = parts[1]
			if len(faces) > 1:
				name = name[:MAX_NAME_LEN-1]
				for i in range(len(faces)):
					db.insert_features(user_id, name + str(i), faces[i])
					count += 1
			else:
				name = name[:MAX_NAME_LEN]
				db.insert_features(user_id, name, faces[0])
				count += 1
	tick('files2db', '2_insert_data')
	db.commit_db()
	print('Inserted {} faces from files'.format(count))


def load_people2db(people, vk_tokens):
	def f_kwargs_db(kwargs):
		kwargs['db'] = DBVk()

	load_people(people, person2db,
		cyclic_args={'vka':vk_tokens},
		kwargs_processors=[f_kwargs_db, f_kwargs_vk])


def find_person(file, db):
	tick('find_person')
	if isinstance(file, str):
		if '.dat' in file:
			file = load_pickle(file)
			if len(file) > 1:
				print('Warning: BytesIO has multiple faces!')
			face = file[0]
		else:
			# Consider path
			face = find_faces(read_files(file))
			if len(face) == 0:
				raise Exception('Photo has no face!')
			elif len(face) > 1:
				print('Warning: Photo has multiple faces!')
			face = face[0]
	elif hasattr(file, 'read'):
		# Consider BytesIO
		face = find_faces(read_files(file))
		if len(face) == 0:
			raise Exception('BytesIO has no face!')
		elif len(face) > 1:
			print('Warning: BytesIO has multiple faces!')
		face = face[0]
	elif hasattr(file, 'size'):
		# File is alrady a numpy array, e.g face
		face = file
	else:
		raise Exception('File must be a path, BytesIO, or NumPy array, but it is ' + str(type(file)))
	tick('find_person', '1_file_load')
	res = db.select_matches(face)
	tick('find_person', '2_select_matches')

	print('Search results: {} related users.'.format(len(res)))
	for row in res:
		print('- Found this person on {} photos with {}% confidence:'.format(row[2], row[1]))
		# if row[1] > 0.5:
		# 	print('- Found this person on {} photos:'.format(row[2]))
		# else:
		# 	print('- Found similar person on {} photos:'.format(row[2]))
		print('http://vk.com/id{}'.format(row[0]))
		print(row[3])
	print()


def find_person_net(path, bits_threshold=None, where=''):
	url = 'http://176.99.9.124:5151/Vk/FindPerson/'
	files = {'image.jpg': open(path,'rb')}
	values = {'where': where}
	if bits_threshold is not None:
		values['bits_threshold'] = bits_threshold
	response = requests.post(url, files=files, data=values)
	data = response.content.decode('utf-8')
	if response.status_code == 200:
		data = json.loads(data)
		return data
	else:
		print('FindPerson bad code: {}, data:<br>\n{}'.format(response.status_code, data))
	return {
		'done': False,
		'comment': 'No response',
	}


def find_person_threshold(path, limit_first, limit_second, id_is=None, id_not=None):
	url = 'http://176.99.9.124:5151/Vk/FindThreshold/'
	files = {'image.jpg': open(path,'rb')}
	where = ''
	if id_is is not None:
		where = 'WHERE user_id = {}'.format(id_not)
	elif id_not is not None:
		where = 'WHERE user_id != {}'.format(id_not)
	values = {
		'limit_first': limit_first,
		'limit_second': limit_second,
		'where' : where,
	}
	response = requests.post(url, files=files, data=values)
	data = response.content.decode('utf-8')
	if response.status_code == 200:
		data = json.loads(data)
		return data
	else:
		print('FindThreshold bad code: {}, data:<br>\n{}'.format(response.status_code, data))
	return {
		'done': False,
		'comment': 'No response',
	}


people = [3118645, 18055874, 2342093, 3553285, 45710415, 17685100, 1359885, 6201582, 30310415, 17439504, xxxxx, 2546032, 38543197, 13552847]


def test_load():
	db = DBVk()
	res = person2db(184639, 7255377, 35462, db=db, vka=VkAccess(VK_TOKEN))
	print(res)
	person2db(people, db=db)
	files2db(db=db, path='xxxxx')

	# vka = VkAccess(VK_TOKEN)
	# people = vka.get_user_friends(139147576)
	# print(len(people))
	# people = vka.filter_recent_users(people)
	# print(len(people))
	# print(people)

	# load_people2db([481100000])
	# load_people2db(people[90:100], [VK_TOKEN])

	# print(db.get_stats())

	# filenames = find_filenames(path, ext='.dat')
	# print(filenames)
	# key = list(filenames.keys())[0]
	# faces = load_pickle(filenames[key])
	# print(faces)

	# find_person('/.../Data/172554877-1nLtTdUUZ48.dat', db=db)


def test_search_net():
	# filename = 'kml.jpg' # 1405851 threshold must be 50
	# filename = 'summer.jpg' # 7255377 threshold must be 46
	filename = 'alwhap.jpg' # 1275247 threshold must be 48

	path = '/.../TestPhotos'
	path = join(path, filename)
	where = ''
	among = [4522, 1407851, 2790, 1275247] + people
	where = 'user_id IN ({})'.format(','.join(map(lambda x: str(x), among)))
	print('- Searching among {} people'.format(len(among)))

	print('- Searching person...')
	res = find_person_net(path, bits_threshold=None, where=where)
	if res['done']:
		for row in res['found']:
			print('- Found this person on {} photos with {}% confidence:'.format(row[2], row[1]))
			print('http://vk.com/id{} / {} / {}'.format(row[0], row[3], row[4]))
	else:
		print(res['comment'])


if __name__ == '__main__':
	me = SingleInstance()
	# test_load()
	test_search_net()

	# tock(pretty=True)


