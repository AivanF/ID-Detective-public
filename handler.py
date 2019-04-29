import time
import threading

from utils import *
from faces import read_files, find_faces, find_face_matches

MAX_NAME_LEN = 4
SKIP_PERSON_COUNT = 2


@multi_all
def load_person(user_id, silent=True, pro=None, f_get_user_photos=None,
		f_save_face=None, f_exists_user_id=None, f_commit=None, **kwargs):
	if pro is not None:
		pro.note('Tried Users', key=True)

	if f_exists_user_id is not None:
		if f_exists_user_id(user_id, kwargs):
			if not silent:
				print('User is already scanned!')
			if pro is not None:
				pro.add()
				pro.note('Already added', key=True)
			return

	try:
		tick('person2db')
		# photos = vka.get_user_photos(user_id, print_urls=0)
		# urls = vka.get_user_photos_urls(user_id)
		urls = f_get_user_photos(user_id, kwargs)
		tick('person2db', '0_get_user_photos_urls')
		photos = bio_download_named(urls)
		if len(photos) == 0:
			if pro is not None:
				pro.note('No photos', key=True)
				pro.add()
			return

		tick('person2db', '1_load_photos')
		photos = read_files(photos)
		tick('person2db', '2_read_files')
		faces = find_faces(photos, limit=5)
		tick('person2db', '3_find_faces')
	except Exception as ex:
		log_ex(ex, 'user_id={}'.format(user_id))
		return

	if len(faces) == 0:
		if pro is not None:
			pro.note('No faces', key=True)
			pro.add()
		return
	for filename in faces:
		if len(faces[filename]) == 1:
			f_save_face(user_id, filename[:MAX_NAME_LEN], faces[filename][0], kwargs)
			pro.note('Faces', key=True)
		else:
			already = []
			for i in range(min(10, len(faces[filename]))):
				face = faces[filename][i]
				if len(already) >= SKIP_PERSON_COUNT:
					count = find_face_matches(already, face)
					if count >= SKIP_PERSON_COUNT:
						pro.note('Skip faces', key=True)
						continue
				f_save_face(user_id, filename[:MAX_NAME_LEN-1] + str(i), face, kwargs)
				already.append(face)
				pro.note('Faces', key=True)
	tick('person2db', '4_insert_data')

	if f_commit is not None:
		f_commit(kwargs)
	if not silent:
		print('Inserted {} faces from user_id {}'.format(count, user_id))
	if pro is not None:
		pro.note('Added Users', key=True)
		pro.add()


def load_people(people, target, pro, kwargs=None, cyclic_args=None, kwargs_processors=None, threads_count=None):
	print('Loading {} people'.format(len(people)))
	tick('load_people')
	tick('load_people', '1_started')
	threads = []
	if threads_count is None or threads_count < 1:
		threads_count = 5

	def run_part(part):
		args = (part,)
		# Thread-specific values
		local_kwargs = {
			'pro': pro,
		}
		if kwargs is not None:
			local_kwargs.update(kwargs)
		# Handy for Vk tokens – the more of them the more threads allowed
		# Token is translated to VkAccess by kwargs_processor
		if cyclic_args is not None:
			for key in cyclic_args:
				l = cyclic_args[key]
				n = len(l)
				if n == 0:
					continue
				elif n == 1:
					local_kwargs[key] = l[0]
				else:
					local_kwargs[key] = l[len(threads) % n]
		if kwargs_processors is not None:
			for cur in kwargs_processors:
				cur(local_kwargs)
		the = threading.Thread(target=target, args=args, kwargs=local_kwargs)
		the.start()
		threads.append(the)
		time.sleep(0.05)

	if len(people) > threads_count:
		ind = 0.0
		step = len(people) / threads_count
		for i in range(threads_count - 1):
			part = people[ int(ind) : int(ind+step) ]
			# print('run {} : {}'.format(int(ind), int(ind+step)))
			ind += step
			run_part(part)
		part = people[ int(ind) : len(people) ]
		# print('run {} : {}'.format(int(ind), len(people)))
		run_part(part)

	else:
		for user_id in people:
			run_part(user_id)

	# print('Started {} threads'.format(len(threads)))
	tick('load_people', '2_all_started')
	for the in threads:
		the.join()
	# print('All threads completed')
	tick('load_people', '3_all_completed')

	pro.show_notes()
	tock(pretty=False)

