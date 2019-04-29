from os.path import join
import requests, json
from vk import VkAccess
from test__utils import get_test_photo, get_test_user

DOMAINS = ['.ru', '.com', '.org']
DEFTOK = 'xxxxx'

ASK_FIELDS = ['domain', 'nickname', 'site']
USE_FIELDS = {'first_name', 'last_name', 'nickname', 'domain', 'site'}


def cut_domain(name):
	if '@' in name:
		name = name.split('@')[0]
	else:
		for cur in DOMAINS:
			if cur in name:
				name = name[name.rfind(cur) + len(cur)+1:]
				break
	return name


class QuerierVk():
	def __init__(self, vka, q=None):
		self.vka = vka
		self.q = None
		self.elements = None
		if q is not None:
			self.parse_query(q)

	def parse_element(self, el):
		res = dict()
		if 'search?' in el:
			res['type'] = 'search'
			res['count'] = 1000
			res['url'] = el
		else:
			ind, kind = self.vka.resolve_name(el)
			if kind is None:
				raise Exception('Object "{}" wasnot found on Vk'.format(el))
			else:
				# TODO: handle URLs
				power = 1
				if '!' in el:
					el = el.split('!')
					power = int(el[1])
					if power > 2 or power < 0:
						raise Exception('Power "{}" is wrong'.format(power))
					el = el[0]
				if kind == 'group':
					data = self.vka.get_group_descr(ind)
					if data is None:
						raise Exception('Group "{}" got None description'.format(el))
					data = data[0]
					res.update(data)
					res['count'] = data['members_count']
				elif kind == 'user':
					data = self.vka.get_user_descr(ind)
					if data is None:
						raise Exception('User "{}" got None description'.format(el))
					data = data[0]
					res.update(data)
					res['count'] = data['counters']['friends']
					res['power'] = power
				else:
					raise Exception('Object "{}" wrong type "{}"'.format(el, kind))
			res['type'] = kind
			res['id'] = ind
		return res

	def parse_query(self, q):
		print('- QuerierVk.parse_query')
		self.q = [x for x in q.split(' ') if len(x) > 0]
		ops = ['+']
		self.elements = []
		for i, el in enumerate(self.q):
			if i % 2 == 1:
				if len(el) > 1:
					raise Exception('Not operator "{}"'.format(el))
				if el not in ops:
					raise Exception('Bad operator "{}"'.format(el))
			else:
				self.q[i] = self.parse_element(el)
				self.elements.append(self.q[i])
		# print('Parsed query:')
		# print('\n'.join([str(x) for x in self.q]))

	def elemnts_apply(self, fun):
		for obj in self.elements:
			if obj['type'] == 'user':
				# TODO: add handling of obj['power']
				vka.get_user_friends(obj['id'], fields=ASK_FIELDS, fun=fun)
			elif obj['type'] == 'group':
				vka.get_group_members(obj['id'], fields=ASK_FIELDS, fun=fun)
			elif obj['type'] == 'search':
				vka.get_users_search_url(obj['url'], fields=ASK_FIELDS, fun=fun)
			else:
				raise Exception('Object "{}" wrong type "{}"'.format(obj, obj['type']))

	def get_among(self):
		# TODO: change to query handling
		res = set()
		def cb_add(people):
			for obj in people:
				# TODO: check that acc is alive and not private
				res.add(obj['id'])
		self.elemnts_apply(cb_add)
		return res


class SearchVk():
	def __init__(self, vka, q=None):
		self.vka = vka
		self.q = q

	def apply_callback(self, fun):
		for key in CHECK_GROUPS:
			self.vka.get_group_members(key, fields=ASK_FIELDS, fun=fun)
		for key in CHECK_USERS:
			self.vka.get_user_friends(key, fields=ASK_FIELDS, fun=fun)
		if SEARCH_URL is not None:
			self.vka.get_users_search_url(SEARCH_URL, fields=ASK_FIELDS, fun=fun)

	def find_photo(self, fl):
		print('- SearchVk.find_photo')
		url = 'http://176.99.9.124:5151/Vk/FindPerson/'
		files = {'image.jpg': fl}
		values = dict() 
		if self.q is not None:
			values['where'] = 'user_id IN ({})'.format(','.join(map(lambda x: str(x), self.q.get_among())))
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

	def compare_face(self, fl, user_id):
		print('- SearchVk.compare_face')
		url = 'http://176.99.9.124:5151/Vk/CompareFace/'
		files = {'image.jpg': fl}
		values = {'user_id': user_id}
		response = requests.post(url, files=files, data=values)
		data = response.content.decode('utf-8')
		if response.status_code == 200:
			data = json.loads(data)
			return data
		else:
			print('CompareFace bad code: {}, data:<br>\n{}'.format(response.status_code, data))
		return {
			'done': False,
			'comment': 'No response',
		}

	def find_str(self, search_str):
		print('- SearchVk.find_str')
		if self.q is None:
			raise Exception('Searching substring needs Query')
		res = dict()
		people_count = [0, 0]
		def cb_search(people):
			for obj in people:
				if obj['id'] in res:
					people_count[1] += 1
					continue
				people_count[0] += 1
				simple = []
				full = []
				for key in obj:
					if key not in USE_FIELDS:
						continue
					val = str(obj[key]).replace(' ', '')
					if len(val) > 0:
						full.append(val)
						if key == 'site':
							val = cut_domain(val)
						simple.append(val)
				if len(simple) > 0:
					checker = ' '.join(simple)
					if search_str in checker:
						# res[obj['id']] = ' '.join(full)
						res[obj['id']] = obj
		self.q.elemnts_apply(cb_search)
		print('Processed people: ' + str(people_count[0]))
		if people_count[1] > 0:
			print('Met doubles: ' + str(people_count[1]))
		print('Found people: ' + str(len(res)))
		return res

	def check_ids(self):
		print('check_ids')
		res = set()
		people_count = [0, 0]
		def cb_add(people):
			for obj in people:
				# TODO: check that acc is alive and not private
				res.add(obj['id'])
		self.apply_callback(cb_add)
		print(res)


def test_search_net(s):
	print('- Searching person...')
	res = s.find_photo(get_test_photo('aralex'))
	if res['done']:
		for row in res['found']:
			print('- Found this person on {} photos with {}%% confidence:'.format(row[2], row[1]))
			print('http://vk.com/id{} / {} / {}'.format(row[0], row[3], row[4]))
	else:
		print(res['comment'])


def test_compare(s):
	fl = get_test_photo()
	user_id = get_test_user()
	res = s.compare_face(fl, user_id)
	print('- Comparing photo with user ' + str(user_id))
	if res['done']:
		print('\t'.join(['name', 'bs', 'ratio']))
		for row in res['found']:
			print('\t'.join(map(str, row[1:])))
	else:
		print(res['comment'])


if __name__ == '__main__':
	vka = VkAccess(DEFTOK)

	Query = 'xxxxx + xxxxx + id356825 +  idfinance'
	#  + search?c%5Bage_from%5D=20&c%5Bage_to%5D=40&c%5Bcity%5D=10&c%5Bcountry%5D=1&c%5Bper_page%5D=40&c%5Bphoto%5D=1&c%5Bschool%5D=45430&c%5Bsection%5D=people
	# q = QuerierVk(vka, Query)
	q = None

	s = SearchVk(vka, q)
	# print(s.find_str('p06'))
	test_search_net(s)
	# test_compare(s)
	pass

