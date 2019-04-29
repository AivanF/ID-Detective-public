from vk import VkAccess

DOMAINS = ['.ru', '.com', '.org']
DEFTOK = 'xxxxx'

ASK_FIELDS = ['domain', 'nickname', 'site']
USE_FIELDS = {'first_name', 'last_name', 'nickname', 'domain', 'site'}


CHECK_GROUPS = []
CHECK_GROUPS += ['hpmor_print']
# CHECK_GROUPS += ['idfinance']

CHECK_USERS = []
CHECK_USERS += [83546842]
# CHECK_USERS += [172554877]

SEARCH_URL = None
# SEARCH_URL = 'https://vk.com/search?c%5Bage_from%5D=20&c%5Bage_to%5D=40&c%5Bcity%5D=10&c%5Bcountry%5D=1&c%5Bper_page%5D=40&c%5Bphoto%5D=1&c%5Bschool%5D=45430&c%5Bsection%5D=people'

# SEARCH_KEY = 'p06'
SEARCH_KEY = 'sup'
# SEARCH_KEY = 'fouren'


def cut_domain(name):
	if '@' in name:
		name = name.split('@')[0]
	else:
		for cur in DOMAINS:
			if cur in name:
				name = name[name.rfind(cur) + len(cur)+1:]
				break
	return name


def apply_callback(vka, fun):
	for key in CHECK_GROUPS:
		vka.get_group_members(key, fields=ASK_FIELDS, fun=fun)
	for key in CHECK_USERS:
		vka.get_user_friends(key, fields=ASK_FIELDS, fun=fun)
	if SEARCH_URL is not None:
		vka.get_users_search_url(SEARCH_URL, fields=ASK_FIELDS, fun=fun)


def check_search_str():
	print('check_search_str')
	vka = VkAccess(DEFTOK)
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
				if SEARCH_KEY in checker:
					res[obj['id']] = ' '.join(full)
	apply_callback(vka, cb_search)
	print('People: ' + str(people_count[0]))
	if people_count[1] > 0:
		print('Doubles: ' + str(people_count[1]))
	print(res)


def check_ids():
	print('check_ids')
	vka = VkAccess(DEFTOK)
	res = set()
	people_count = [0, 0]
	def cb_add(people):
		for obj in people:
			# TODO: check that acc is alive and not private
			res.add(obj['id'])
	apply_callback(vka, cb_add)
	print(res)


def check_tokens():
	res = VkAccess.describe_tokens([DEFTOK])
	print(res[DEFTOK])


def check_counts():
	print('check_counts')
	vka = VkAccess(DEFTOK)
	# res = vka.to_dict(vka.get_group_descr(CHECK_GROUPS))
	res = vka.to_dict(vka.get_user_descr(CHECK_USERS))
	print(res)


def parse_element(vka, el):
	res = dict()
	if 'search?' in el:
		res['type'] = 'search'
		res['count'] = 1000
		res['q'] = el
	else:
		ind, kind = vka.resolve_name(el)
		if kind is None:
			raise Exception('Object "{}" wasnot found on Vk'.format(el))
		else:
			if kind == 'group':
				data = vka.get_group_descr(ind)
				if data is None:
					raise Exception('Group "{}" got None description'.format(el))
				data = data[0]
				res.update(data)
				res['count'] = data['members_count']
			elif kind == 'user':
				data = vka.get_user_descr(ind)
				if data is None:
					raise Exception('User "{}" got None description'.format(el))
				data = data[0]
				res.update(data)
				res['count'] = data['counters']['friends']
			else:
				raise Exception('Object "{}" wrong type "{}"'.format(el, str(kind)))
		res['type'] = kind
		res['id'] = ind
	return res


def parse_query():
	print('parse_query')
	vka = VkAccess(DEFTOK)
	q = 'id83546842 +  idfinance + search?c%5Bage_from%5D=20&c%5Bage_to%5D=40&c%5Bcity%5D=10&c%5Bcountry%5D=1&c%5Bper_page%5D=40&c%5Bphoto%5D=1&c%5Bschool%5D=45430&c%5Bsection%5D=people'
	q = [x for x in q.split(' ') if len(x) > 0]
	ops = ['+']
	for i, el in enumerate(q):
		if i % 2 == 1:
			if len(el) > 1:
				raise Exception('Not operator "{}"'.format(el))
			if el not in ops:
				raise Exception('Bad operator "{}"'.format(el))
		else:
			q[i] = parse_element(vka, el)
	print('Parsed query:')
	print('\n'.join([str(x) for x in q]))


if __name__ == '__main__':
	# check_search_str()
	# check_ids()
	# check_url()
	# check_tokens()
	check_counts()
	# parse_query()
	pass

