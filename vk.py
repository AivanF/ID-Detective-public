from threading import Lock
import json, urllib, requests
from utils import *
import time

PHOTOS_LOAD = 30
PHOTOS_KEEP = 10
RECENT_MONTHES = 2
BASE_VK_URL = 'https://api.vk.com/method/'
# https://vk.com/dev/api_requests
WAIT_TIME = 0.5

PERMS = {
	'notify': 1,
	'friends': 2,
	'photos': 4,
	'audio': 8,
	'video': 16,
	'stories': 64,
	'pages': 128,
	'status': 1024,
	'notes': 2048,
	'messages': 4096,
	'wall': 8192,
	'ads': 32768,
	'offline': 65536,
	'docs': 131072,
	'groups': 262144,
	'notifications': 524288,
	'stats': 1048576,
	'email': 4194304,
	'market': 134217728,
}

prev__ = {}
mutexes = {}
megamutex = Lock()


# def error_no_resp(data):
# 	txt = '- Vk Error in {}: NO response:\n{}'.format(whosdaddy(), data)
# 	print(txt)
# 	log_er(txt)

# def error_bad_code(status_code, data):
# 	txt = '- Vk Error in {}: bad status_code: {}\n{}'.format(whosdaddy(), status_code, data)
# 	print(txt)
# 	log_er(txt)


"""
Example:
		Old
New	300	600	1200
300	0	-	-
600	+	0	+
1200	+	-	0

Old New Res
600 700  +
"""
SZ_MN = 400
SZ_MX = 700

def find_best_img(img):
	url = None
	w, h, mn = 0, 0, 0
	# album_id PROFILE=-6, WALL=-7
	for size in img['sizes']:
		new_mn = min(size['width'], size['height'])
		save = False
		if url is None:
			save = True
		elif new_mn > mn:
			if mn >= SZ_MN:
				if new_mn < SZ_MX:
					save = True
			else:
				save = True
		elif new_mn >= SZ_MN and mn > SZ_MX:
			save = True
		if save:
			url = size['url']
			w, h = size['width'], size['height']
			mn = new_mn
	return w, h, img['album_id'], url


class VkAccess(object):
	"""Provides access to Vk social network to handle users and photos."""
	def __init__(self, token, printit=False):
		self.token = token
		self.printit = printit
		self.pro = None
		megamutex.acquire()
		if self.token not in mutexes:
			mutexes[self.token] = Lock()
		megamutex.release()


	def vkapi_params(self, args=None):
		if not args:
			args = {}
		args['access_token'] = self.token
		args['v'] = '5.87'
		args['lang'] = 'ru'
		return args


	def check_prev(self):
		# return
		mutexes[self.token].acquire()
		if self.token in prev__:
			if time.time() - prev__[self.token] < WAIT_TIME:
				# print('Waiting')
				time.sleep(WAIT_TIME)
		prev__[self.token] = time.time()
		mutexes[self.token].release()


	def get(self, method, args=None):
		self.check_prev()
		response = requests.get(BASE_VK_URL + method + '?' + urllib.parse.urlencode(self.vkapi_params(args)))
		data = response.content.decode('utf-8')
		if self.printit:
			print('- ' + method + ':')
			print(data)
		if response.status_code == 200:
			data = json.loads(data)
			if 'response' in data:
				return data['response']
			else:
				txt = '- Vk Error in {}: NO response:\n{}'.format(method, data)
				print(txt)
				log_er(txt)
		else:
			txt = '- Vk Error in {}: bad status_code: {}\n{}'.format(method, status_code, data)
			print(txt)
			log_er(txt)
		return None

		
	@obj_multi_all
	def get_user_photos_urls(self, user_id):
		# Returns a list with photo urls
		# print('get_user_photos({})'.format(user_id))
		self.check_prev()
		args = {
			'owner_id': user_id,
			'count': PHOTOS_LOAD,
		}
		response = requests.get(BASE_VK_URL + 'photos.getAll' + '?' + urllib.parse.urlencode(self.vkapi_params(args)))
		data = response.content.decode('utf-8')
		if response.status_code == 200:
			data = json.loads(data)
			if 'response' in data:
				data = data['response']
				res = []
				for img in data['items']:
					cur = find_best_img(img)
					if cur[3] is not None:
						res.append(cur)
				res.sort(key=lambda x: x[2], reverse=True)
				res = res[:PHOTOS_KEEP]
				res = list(map(lambda x: x[3], res))
				return res
			else:
				done = False
				if self.pro is not None:
					if 'error' in data:
						cur = data['error']
						if 'error_msg' in cur:
							self.pro.note(cur['error_msg'], 'vk.error')
							# print(cur['error_msg'])
							done = True
				if not done:
					txt = '- Vk Error in photos.getAll: NO response:\n{}'.format(data)
					print(txt)
					log_er(txt)
		else:
			txt = '- Vk Error in photos.getAll: bad status_code: {}\n{}'.format(status_code, data)
			print(txt)
			log_er(txt)
		return []


	@obj_multi_all
	def get_user_photos(self, user_id, print_urls=False):
		urls = self.get_user_photos_urls(user_id)
		if print_urls:
			print(urls)
		res = {}
		for url in urls:
			if url is None:
				log_er('- Vk url is None user_id {}'.format(user_id))
				continue
			bio = bio_download(url)
			# key = '{}-{}'.format(user_id, bio.name.split('.')[0])
			key = bio.name.split('.')[0]
			res[key] = bio
		return res


	def get_user_friends__(self, user_id, fields=None, fun=None, count=0, offset=0):
		# https://vk.com/dev/friends.get
		# Returns a list with user_id's
		args = {
			'user_id': user_id,
		}
		if fields is not None:
			# ['nickname', 'domain']
			args['fields'] = ','.join(fields)
		if count > 0:
			args['count'] = count
			args['offset'] = offset

		data = self.get('friends.get', args)
		if data is not None and 'items' in data:
			data = data['items']
			if fun is not None:
				fun(data)
			return data
		if fun is None:
			return []

	@obj_multi_all
	def get_user_friends(self, user_id, fields=None, fun=None):
		maxy = 995
		off = 0
		res = []
		while True:
			cur = self.get_user_friends__(user_id, fields=fields, fun=fun, count=maxy, offset=off)
			if fun is None:
				res += cur
			if len(cur) < maxy:
				break
			off += maxy
		return res

	def get_user_descr(self, user_ids, fields=None):
		# https://vk.com/dev/users.get
		if not isiter(user_ids):
			user_ids = (user_ids,)
		args = {
			'user_ids': ','.join(map(lambda x: str(x), user_ids)),
		}
		if fields is None:
			fields = ['counters']
		if fields is not None:
			# id, name, screen_name, is_closed (2 is private), deactivated
			args['fields'] = ','.join(fields)

		data = self.get('users.get', args)
		if data is not None:
			return data
		return []


	def get_group_members__(self, group_id, fields=None, fun=None, count=0, offset=0):
		# https://vk.com/dev/groups.getMembers
		# Returns a list with user_id's
		args = {
			'group_id': group_id,
		}
		if fields is not None:
			args['fields'] = ','.join(fields)
		if count > 0:
			args['count'] = count
			args['offset'] = offset

		data = self.get('groups.getMembers', args)
		if data is not None and 'items' in data:
			data = data['items']
			if fun is not None:
				fun(data)
			return data
		if fun is None:
			return []

	@obj_multi_all
	def get_group_members(self, group_id, fields=None, fun=None):
		maxy = 995
		off = 0
		res = []
		while True:
			cur = self.get_group_members__(group_id, fields=fields, fun=fun, count=maxy, offset=off)
			if fun is None:
				res += cur
			if len(cur) < maxy:
				break
			off += maxy
		return res

	def get_group_descr(self, group_id, fields=None):
		# https://vk.com/dev/groups.getById
		args = {}
		if isiter(group_id):
			args['group_ids'] = ','.join(group_id)
		else:
			args['group_id'] = str(group_id)
		if fields is None:
			fields = ['members_count']
		if fields is not None:
			# id, name, screen_name, is_closed (2 is private), deactivated
			args['fields'] = ','.join(fields)

		data = self.get('groups.getById', args)
		if data is not None:
			return data
		return []


	def get_users_search(self, params, fields=None, fun=None, count=1000, offset=0):
		# https://vk.com/dev/users.search
		# Returns a list with user_id's
		# print('get_users_search(count={}, offset={})'.format(count, offset))
		args = {
			'count': count,
			'offset': offset,
		}
		args.update(params)
		if fields is not None:
			args['fields'] = ','.join(fields)

		data = self.get('users.search', args)
		if data is not None and 'items' in data:
			data = data['items']
			if fun is not None:
				fun(data)
			return data
		if fun is None:
			return []

	# def get_users_search_meta(self, params, fields=None, fun=None, count=5000):
	# 	maxy = 995
	# 	off = 0
	# 	res = []
	# 	while True:
	# 		cur = self.get_users_search__(params, fields=fields, fun=fun, count=maxy, offset=off)
	# 		off += maxy
	# 		if fun is None:
	# 			res += cur
	# 		if off >= count or len(cur) < maxy/2:
	# 			print('{} >= {} or {} < {}'.format(off, count, len(cur), maxy))
	# 			break
	# 	return res

	def get_users_search_url(self, url, *args, **kwargs):
		data = url.split('search?')
		if len(data) != 2:
			return []
		data = data[1]
		data = data.replace('c%5B', '').replace('%5B', '').replace('%5D', '').split('&')
		params = {}
		for pair in data:
			pair = pair.split('=')
			if len(pair) == 2:
				params[pair[0]] = pair[1]
		params.pop('section')
		return self.get_users_search(params, *args, **kwargs)


	def filter_recent_users__(self, user_ids):
		# no more 1000!
		fields = [
			'last_seen',
			# 'followers_count',
			# 'interests',
			# 'connections',
		]
		args = {
			'user_ids': ','.join(map(str, user_ids)),
			'fields': ','.join(fields)
		}

		data = self.get('users.get', args)
		if data is not None:
			now = int(time.time())
			res = []
			for cur in data:
				if 'last_seen' in cur:
					# TODO: last_seen has platform which can tell about user device
					ago = now-cur['last_seen']['time']
					ago /= 3600
					ago /= 24
					ago /= 30.5
					# print(cur)
					# print('- {} {}'.format(cur['first_name'], cur['last_name']))
					# print('{}: {:.4f}'.format(cur['id'], ago))
					if ago < RECENT_MONTHES:
						res.append(cur['id'])
			return res
		return []


	def filter_recent_users(self, user_ids):
		maxy = 995
		if len(user_ids) <= maxy:
			return self.filter_recent_users__(user_ids)
		else:
			cur = 0
			res = []
			while cur < len(user_ids):
				res += self.filter_recent_users__(user_ids[cur:cur+maxy])
				cur += maxy
			return res


	def resolve_name(self, name):
		args = {
			'screen_name': str(name)
		}
		data = self.get('utils.resolveScreenName', args)
		if data is not None:
			if 'object_id' in data and 'type' in data:
				return data['object_id'], data['type']
			else:
				return -1, None
		return None, None


	def get_user_id(self):
		ind, name = None, None
		data = self.get('users.get')
		if data is not None:
			for cur in data:
				# print(cur)
				ind = cur['id']
				name = '{} {}'.format(cur['last_name'], cur['first_name'])
		return ind, name


	def get_app_id(self):
		ind, name = None, None
		data = self.get('apps.get')
		if data is not None:
			for cur in data['items']:
				if 'id' in cur:
					ind = cur['id']
					name = cur['title']
		return ind, name


	def get_perms(self):
		res = None
		data = self.get('account.getAppPermissions')
		if data is not None:
			data = int(data)
			res = []
			for cur in PERMS:
				if data & PERMS[cur]:
					res.append(cur)
		return res


	@classmethod
	def describe_tokens(cls, values, visual=False):
		res = {}
		for cur in values:
			vka = cls(cur)
			user_id, user_name = vka.get_user_id()
			app_id, app_name = vka.get_app_id()
			perms = vka.get_perms()
			if user_id is not None and app_id is not None:
				res[cur] = {
					'good': True,
					'perms': perms,
					'user_id': user_id,
					'user_name': user_name,
					'app_id': app_id,
					'app_name': app_name,
				}
			else:
				res[cur] = { 'good': False }
		return res


	def to_dict(self, ar, key='id'):
		res = {}
		for obj in ar:
			res[obj[key]] = obj
		return res


def f_get_user_photos(user_id, kwargs):
	return kwargs['vka'].get_user_photos_urls(user_id)


def f_kwargs_vk(kwargs):
	kwargs['vka'] = VkAccess(kwargs['vka'])
	kwargs['vka'].pro = kwargs['pro']

