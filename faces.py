# https://github.com/ageitgey/face_recognition
import face_recognition
from os import getcwd
from os.path import isfile, join
from utils import *

CWD = getcwd()
PATH_IMG = join(CWD, 'Cat')
PATH_DATA = join(CWD, 'Data')


def read_files(data):
	# Can use file names or file-like objects
	# Returns numpy array
	if isinstance(data, str) or hasattr(data, 'read'):
		return face_recognition.load_image_file(data)
	elif isinstance(data, dict):
		files = {}
		for key in data:
			fl = face_recognition.load_image_file(data[key])
			files[key] = fl
		return files
	else:
		raise Exception('Data must be a path or BytesIO or a dict with them, but it is ' + str(type(file)))


CAN_LOAD = False
# CAN_SAVE = True
CAN_SAVE = False


def find_faces(data, limit=None):
	if hasattr(data, 'size'):
		# Consider file is a numpy array
		return face_recognition.face_encodings(data)
	elif isinstance(data, dict):
		faces = {}
		done = 0
		for key in data:
			dat_file = join(PATH_DATA, key + '.dat')
			if CAN_LOAD and isfile(dat_file):
				faces[key] = load_pickle(dat_file)
			else:
				if limit is not None:
					if done >= limit:
						break
				found = face_recognition.face_encodings(data[key])
				if len(found) > 0:
					done += len(found)
					faces[key] = found
					if CAN_SAVE:
						save_pickle(dat_file, found)
		return faces
	elif hasattr(data, '__iter__'):
		res = []
		for file in data:
			res += face_recognition.face_encodings(file)
		return res
	else:
		raise Exception('Data must be a BytesIO or container with such objects, but it is ' + str(type(file)))


def find_face_matches(data, target):
	return sum(face_recognition.compare_faces(data, target, tolerance=0.54))


def compare_my(faces, target):
	if target not in faces:
		print('Target file "{}" has no faces!'.format(target))
	else:
		# debugit(faces[target])
		encodings = []
		names = []
		for key in faces:
			if key != target:
				if len(faces[key]) > 1:
					for i in range(len(faces[key])):
						encodings.append(faces[key][i])
						names.append(key + '_' + str(i))
				else:
					encodings.append(faces[key][0])
					names.append(key)
		results = face_recognition.compare_faces(encodings, faces[target][0], tolerance=0.53)
		count = 0
		print('Comparison with "{}":'.format(target))
		for i in range(len(results)):
			curres = results[i]
			curname = names[i]
			print('- "{}": {}'.format(curname, curres))
			if curres:
				count += 1
		print('In total: {} matches'.format(count))


if __name__ == '__main__':
	tick('main')
	print('Started')
	filenames = find_filenames(PATH_IMG, ext='.jpg')
	files = read_files(filenames)
	print('Loaded files...')
	tick('main', 'loading')
	faces = find_faces(files)
	print('Detected faces...')
	tick('main', 'detecting')
	compare_my(faces, 'winter')
	tick('main', 'comparing')
	tock(pretty=True)

