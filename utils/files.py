
# import uuid
from os import listdir
from os.path import basename, join, isfile
from io import BytesIO
import pickle, json, requests
from .decor import multi_first, multi_all


def read_json(path):
	with open(path, 'r') as f:
		return json.loads(f.read())


def save_json(path, data):
	with open(path, 'w') as f:
		f.write(json.dumps(data))


def load_pickle(path):
	if isinstance(path, str):
		with open(path, 'rb') as f:
			return pickle.load(f)
	elif hasattr(path, 'read'):
		# Consider it is a BytesIO
		return pickle.load(path)
	else:
		raise Exception('Value must be a path or BytesIO, but it is ' + str(type(file)))


def save_pickle(path, data):
	with open(path, 'wb') as f:
		pickle.dump(data, f)


def find_filenames(path, ext=''):
	# Returns dict with pathes
	names = [f for f in listdir(path) if ext in f and isfile(join(path, f))]
	res = {}
	for f in names:
		res[f] = join(path, f)
		# res[f.split('.')[0]] = join(path, f)
	return res


@multi_first
def bio_download(url):
	# print('bio_download:\n' + url)
	r = requests.get(url, stream=True)
	if r.status_code == 200:
		bio = BytesIO()
		bio.name = basename(url)
		for chunk in r:
			bio.write(chunk)
		bio.seek(0)
		# print(len(bio.read()))
		return bio


def bio_download_named(urls):
	# URLs is a list
	# Returns a dict of BytesIO objects
	res = {}
	for url in urls:
		if url is None or len(url) < 10:
			continue
		bio = bio_download(url)
		# str(uuid.uuid4())
		if bio is not None:
			key = bio.name.split('.')[0]
			res[key] = bio
	return res


@multi_first
def bio_save(bio, path):
	with open(join(path, bio.name), 'wb') as fl:
		fl.write(bio.read())


if __name__ == '__main__':
	data = 'https://pp.userapi.com/c846523/v846523309/b087c/YQ1Clobi5Bg.jpg'
	# data = [data, 'https://pp.userapi.com/c636524/v636524005/2f78b/cFVGC5dzbfI.jpg']

	print(bio_download(data))

