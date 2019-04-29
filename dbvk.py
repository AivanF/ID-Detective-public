# https://github.com/ageitgey/face_recognition/issues/238#issuecomment-345847465
# https://dev.mysql.com/doc/refman/8.0/en/miscellaneous-functions.html#function_inet-ntoa
# import atexit
import time
import MySQLdb
from utils import *

# GRANT ALL PRIVILEGES ON *.* TO 'faceproj'@'localhost' INDENTIFIED BY 'f@c2.71R' WITH GRANT OPTION
# faceproj	f@c2.71R
# GRANT ALL PRIVILEGES ON faces.* TO 'faceproj'@'localhost';
# CREATE USER 'faceproj'@'localhost' IDENTIFIED WITH mysql_native_password BY 'f@c2.71R';

hidden_data = {}
BYTE = 8
FEATURES_COUNT = 128
# FEATURES_COUNT = 2
WORKER_NAME_LEN = 8
MAX_NAME_LEN = 4
FLOAT_TYPE = 'FLOAT'
# FLOAT_TYPE = 'DOUBLE'
DATABASE_NAME = 'faces'


def check_features_names():
	if 'feature_names' not in hidden_data:
		temp = ['f' + str(i) for i in range(FEATURES_COUNT)]
		hidden_data['feature_names'] = ', '.join(temp)
	return hidden_data['feature_names']


# def check_compare_args():
# 	if 'compare_args' not in hidden_data:
# 		temp = ['a' + str(i) for i in range(FEATURES_COUNT)] + ['b' + str(i) for i in range(FEATURES_COUNT)]
# 		hidden_data['compare_args'] = ', '.join(temp)


def bit_hash(values):
	if len(values) != FEATURES_COUNT:
		raise Exception('bit_hash: wrong values length! It is {}, need {}'.format(len(values), FEATURES_COUNT))
	res = []
	byte = 0
	cnt = 0
	def add(b):
		nonlocal res, byte, cnt
		byte = (byte << 1) + b
		cnt += 1
		if cnt == BYTE:
			res.append(byte)
			cnt = 0
			byte = 0
	for el in values:
		add(int(el >= 0.1))
		add(int(el <= -0.1))
	return bytes(res)


ids_cnt = 0

class DBVk(object):
	"""Provides simple access to MySQL DB to handle faces of Vk users."""
	def __init__(self):
		self.__db = None
		self.__cursor = None
		global ids_cnt
		self.id = ids_cnt
		ids_cnt += 1
		self.init_db()

	def init_db(self):
		# print('Init DBVk #{}'.format(self.id))
		self.__db = MySQLdb.connect(host='localhost', user='faceproj', passwd='f@c2.71R')
		self.__cursor = self.__db.cursor()
		self.use_db()
		# print('DBVk.init #{}'.format(self.id))

		# def callback():
		# 	# print('DBVk.callback #{}'.format(self.id))
		# 	self.close_db()
		# atexit.register(callback)

	def __del__(self):
		self.close_db()

	def use_db(self):
		self.execute('USE {};'.format(DATABASE_NAME))

	def execute(self, query):
		if self.__cursor is None:
			raise Exception('DB was not initialised!')
		# global __cursor
		# if __cursor is not None:
		# 	__cursor.close()
		# __cursor = __db.cursor()
		self.__cursor.execute(query)

	def fetchall(self):
		return self.__cursor.fetchall()

	def commit_db(self):
		self.__db.commit()

	def close_db(self):
		if self.__db is not None:
			self.__db.close()
			# print('\tDB is closed')
			self.__cursor = None
			self.__db = None

	def get_dbs(self):
		self.execute('SHOW DATABASES;')
		return [row[0] for row in self.fetchall()]

	def get_tables(self):
		self.execute('SHOW TABLES;')
		return [row[0] for row in self.fetchall()]

	def describe_table(self, name):
		self.execute('describe {}'.format(name))
		res = {}
		for row in self.fetchall():
			res[row[0]] = ' '.join([str(el) for el in row[1:] if el is not None and len(str(el)) > 1])
			res[row[0]] = {
				'type': row[1],
				# 'null': row[2],
				# 'key': row[3],
				# 'default': row[4],
			}
		return res

	def create_table_faces(self):
		if 'VkUsers' in self.get_tables():
			query = 'DROP TABLE IF EXISTS `VkUsers`;'
			self.execute(query)
			print('VkUsers table was deleted!!!')
		query = """\
CREATE TABLE `VkUsers` (
`user_id` INT(4) UNSIGNED NOT NULL,
`name` VARCHAR({}) NOT NULL,
`mask` BINARY(32) NOT NULL\n""".format(MAX_NAME_LEN)

		for i in range(FEATURES_COUNT):
			query += '`f{}` {} NOT NULL,\n'.format(i, FLOAT_TYPE)

		query += """\
PRIMARY KEY (`user_id`, `name`)
) CHARSET=UTF8MB4;"""
		self.execute(query)
		print('Main table created!')

	def create_table_tasks(self):
		if 'VkTasks' in self.get_tables():
			query = 'DROP TABLE IF EXISTS `VkTasks`;'
			self.execute(query)
			print('VkTasks table was deleted!!!')
		# down is included, up is excluded
		query = """\
CREATE TABLE `VkTasks` (
`id` INT(4) UNSIGNED NOT NULL,
`worker` VARCHAR({}) NOT NULL,
`ip` VARBINARY(16) NOT NULL,
`down` INT(4) UNSIGNED NOT NULL,
`up` INT(4) UNSIGNED NOT NULL,
`expire` TIMESTAMP NOT NULL,
PRIMARY KEY (`id`)
) CHARSET=UTF8MB4;""".format(WORKER_NAME_LEN)
		self.execute(query)
		print('Table created!')

	def select_faces_count(self):
		query = 'SELECT COUNT(*) AS cnt FROM VkUsers;'
		self.execute(query)
		return self.fetchall()[0][0]

	# def select_faces(self, limit=10):
	# 	query = 'SELECT user_id, name, f0, f1 FROM VkUsers LIMIT {};'.format(limit)
	# 	self.execute(query)
	# 	return self.fetchall()

	def insert_features(self, user_id, name, values):
		if len(values) != FEATURES_COUNT:
			raise Exception('Wrong features count!')
		mask = bit_hash(values).hex()
		str_values = ', '.join(map(str, values))
		# print('Inserting with mask {}'.format(mask))
		check_features_names()
		name = name[:MAX_NAME_LEN]
		query = 'INSERT INTO VkUsers (user_id, name, mask, {}) VALUES ({}, "{}", UNHEX("{}"), {});'
		query = query.format(hidden_data['feature_names'], user_id, name, mask, str_values)
		try:
			self.execute(query)
		except MySQLdb.IntegrityError as ex:
			if 'Duplicate entry' in str(ex):
				pass
				# query = 'UPDATE VkUsers SET mask=UNHEX("{}") WHERE user_id = {}, name = "{}"'
				# print('Duplicate feature {}-{}'.format(user_id, name))
			else:
				raise ex

	def create_function(self):
		query = 'DROP FUNCTION IF EXISTS f_difference;'
		self.execute(query)
		arg_names  = ['a' + str(i) + ' ' + FLOAT_TYPE for i in range(FEATURES_COUNT)]
		arg_names += ['b' + str(i) + ' ' + FLOAT_TYPE for i in range(FEATURES_COUNT)]
		values = ['power(a{}-b{},2)'.format(i,i) for i in range(FEATURES_COUNT)]
		query = """\
		CREATE FUNCTION f_difference ({})
		RETURNS FLOAT DETERMINISTIC
		RETURN sqrt({});\
		""".format(', '.join(arg_names), ' + '.join(values))
		# RETURN sqrt({});\

		# print(query)
		self.execute(query)
		print('F.difference created!')


	def select_threshold(self, values=None, mask=None, limit_first=10000, limit_second=50, where=''):
		if mask is None:
			if values is None:
				raise Exception('select_threshold need either values or mask arg!')
			if len(values) != FEATURES_COUNT:
				raise Exception('Wrong features count!')
			mask = bit_hash(values).hex()

		if len(where) > 1:
			where = 'WHERE ' + where

		args = {
			'mask': mask,
			'where': where,
			'limit_first': limit_first,
			'limit_second': limit_second,
		}

		# print('- Searching bits threshold {limit_first} : {limit_second}'.format(**args))
		query = """
		SELECT MIN(matched_bits) AS down, CAST(FLOOR(AVG(matched_bits)) AS UNSIGNED) AS mean, MAX(matched_bits) AS up
		FROM (
			SELECT matched_bits
			FROM (
				SELECT BIT_COUNT(mask & UNHEX('{mask}')) AS matched_bits
				FROM VkUsers {where}
				LIMIT {limit_first}
			) AS t1
			ORDER BY matched_bits DESC
			LIMIT {limit_second}
		) AS t2
		;""".format(**args)

		try:
			self.execute(query)
		except Exception as ex:
			print(query)
			raise ex

		for cur in self.fetchall():
			return list(cur)
		raise Exception('select_threshold no result!')


	def select_matches(self, values, bits_threshold=None, where='', ratio_min=0.52):
		check_features_names()
		if len(values) != FEATURES_COUNT:
			raise Exception('Wrong features count!')		
		str_values = ', '.join(map(str, values))
		mask = bit_hash(values).hex()
		# print(mask)

		if bits_threshold is None:
			bits_matches = self.select_threshold(mask=mask, limit_first=10000, limit_second=50, where=where)
			# use average
			bits_threshold = bits_matches[1]
			print('- Selected threshold: {} bits'.format(bits_threshold))
		else:
			print('- Using given threshold: {} bits'.format(bits_threshold))

		if len(where) > 1:
			where = 'WHERE ' + where
		args = {
			'ratio_min': ratio_min,
			'bits_threshold': bits_threshold,
			'feature_names': hidden_data['feature_names'],
			'str_values': str_values,
			'mask': mask,
			'where': where,
		}

		# print('- Searching with bruteforce. Warning! It is too slow')
		# query = """
		# SELECT user_id, MAX(ratio) AS ratio, COUNT(*) AS cnt, GROUP_CONCAT(name SEPARATOR ' ') AS names
		# FROM (
		# 	SELECT user_id, name, 1.0-f_difference({feature_names}, {str_values}) AS ratio
		# 	FROM VkUsers
		# 	HAVING ratio > {ratio_min}
		# ) AS t
		# GROUP BY user_id
		# ORDER BY ratio DESC
		# LIMIT 10
		# ;""".format(**args)

		# print('- Searching with Hash 1 PLAIN')
		# query = """
		# SELECT user_id, MAX(ratio) AS ratio, COUNT(*) AS cnt, GROUP_CONCAT(name SEPARATOR ' ') AS names, GROUP_CONCAT(matched_bits SEPARATOR ' ') AS matched_bits
		# FROM (
		# 	SELECT user_id, name, 1.0-f_difference({feature_names}, {str_values}) AS ratio, matched_bits
		# 	FROM (
		# 		SELECT user_id, name, {feature_names}, BIT_COUNT(mask & UNHEX('{mask}')) AS matched_bits
		# 		FROM VkUsers {where}
		# 		HAVING matched_bits >= {bits_threshold}
		# 	) AS basic
		# 	HAVING ratio > {ratio_min}
		# ) AS t
		# GROUP BY user_id
		# ORDER BY ratio DESC
		# LIMIT 10
		# ;""".format(**args)

		print('- Searching with Hash 2 JOIN')
		query = """
		SELECT user_id, MAX(ratio) AS ratio, COUNT(*) AS cnt, GROUP_CONCAT(name SEPARATOR ' ') AS names, GROUP_CONCAT(matched_bits SEPARATOR ' ') AS matched_bits
		FROM (
			SELECT t1.user_id AS user_id, t1.name AS name, 1.0-f_difference({feature_names}, {str_values}) AS ratio, matched_bits
			FROM (
				SELECT user_id, name, BIT_COUNT(mask & UNHEX('{mask}')) AS matched_bits
				FROM VkUsers {where}
				HAVING matched_bits >= {bits_threshold}
			) AS t1
			LEFT JOIN (
				SELECT user_id, name, {feature_names}
				FROM VkUsers
			) AS t2
			ON t1.user_id = t2.user_id AND t1.name = t2.name
			HAVING ratio > {ratio_min}
		) AS t
		GROUP BY user_id
		ORDER BY ratio DESC
		LIMIT 10
		;""".format(**args)

		try:
			self.execute(query)
		except Exception as ex:
			print(query)
			raise ex

		res = []
		for cur in self.fetchall():
			row = list(cur)
			row[1] = clamp_percent(row[1])
			row[3] = row[3].split(' ')
			res.append(row)
		return res


	def select_compare(self, values, user_id):
		check_features_names()
		if len(values) != FEATURES_COUNT:
			raise Exception('Wrong features count!')		
		str_values = ', '.join(map(str, values))
		mask = bit_hash(values).hex()
		# print(mask)

		args = {
			'feature_names': hidden_data['feature_names'],
			'str_values': str_values,
			'mask': mask,
			'user_id': user_id,
		}

		print('- Comparing face with user')
		query = """
		SELECT user_id, name
			, BIT_COUNT(mask & UNHEX('{mask}')) AS matched_bits
			, 1.0-f_difference({feature_names}, {str_values}) AS ratio
		FROM VkUsers
		WHERE user_id = {user_id}
		LIMIT 10
		;""".format(**args)

		try:
			self.execute(query)
		except Exception as ex:
			print(query)
			raise ex

		res = []
		for cur in self.fetchall():
			row = list(cur)
			row[3] = clamp_percent(row[3])
			# row[3] = clamp_percent(row[3], 0, 100)
			res.append(row)
		return res


	def exists_user_id(self, user_id):
		query = 'SELECT COUNT(*) FROM VkUsers WHERE user_id = ' + str(user_id)
		self.execute(query)
		return self.fetchall()[0][0] > 0

	# def select_user_ids(self):
	# 	query = 'SELECT DISTINCT user_id FROM VkUsers ORDER BY user_id ASC;'
	# 	self.execute(query)
	# 	return [row[0] for row in self.fetchall()]

	def select_user_count(self):
		# query = 'SELECT COUNT(*) FROM (SELECT DISTINCT user_id FROM VkUsers) AS t;'
		query = 'SELECT COUNT(DISTINCT user_id) AS cnt FROM VkUsers'
		self.execute(query)
		return self.fetchall()[0][0]

	def select_sizes(self):
		query = """
SELECT table_schema AS "Database", ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS "Size MB"
FROM information_schema.TABLES 
GROUP BY table_schema;"""
		self.execute(query)
		for row in self.fetchall():
			if row[0] == DATABASE_NAME:
				return row[1]
		return None

	def select_task_id(self, ind):
		query = """
SELECT worker, INET_NTOA(ip) AS ip, down, up, expire
FROM VkTasks WHERE id = {}""".format(ind)
		self.execute(query)
		res = self.fetchall()
		if len(res) > 0:
			return self.read_row(res[0], ['worker', 'ip', 'down', 'up', 'expire'])
		else:
			return None

	def select_task_new(self):
		query = 'SELECT MIN(id) AS mn, MAX(id) AS mx, MAX(up) AS up FROM VkTasks'
		self.execute(query)
		res = self.fetchall()[0]
		mn = res[0]
		mx = res[1]
		if mn is None:
			ind = 0
			down = 1
		else:
			down = res[2] + 1
			if mn > 1:
				ind = mn - 1
			else:
				ind = mx + 1
		return ind, down

	def select_task_free(self):
		now = int(time.time())
		query = """
SELECT id, worker, INET_NTOA(ip) AS ip, down, up
FROM VkTasks WHERE expire < FROM_UNIXTIME({}) AND down < up
ORDER BY down DESC
LIMIT 1""".format(now)
		self.execute(query)
		res = self.fetchall()
		if len(res) > 0:
			return self.read_row(res[0], ['id', 'worker', 'ip', 'down', 'up'])
		else:
			return None

	def select_task_debt(self, worker):
		query = """
SELECT id, worker, INET_NTOA(ip) AS ip, down, up, expire
FROM VkTasks WHERE worker="{}" AND down < up
""".format(worker)
		self.execute(query)
		res = self.fetchall()
		if len(res) > 0:
			return self.read_row(res[0], ['id', 'worker', 'ip', 'down', 'up', 'expire'])
		else:
			return None

	# def count_task_debt(self, ip, worker):
	# 	now = int(time.time())
	# 	query = 'SELECT COUNT(*) AS cnt FROM VkTasks WHERE (worker="{}" OR ip=INET_ATON("{}")) AND down < up'.format(worker, ip)
	# 	self.execute(query)
	# 	return self.fetchall()[0][0]

	def insert_task(self, ind, worker, ip, down, up, expire=None, days=None):
		if expire is None:
			if days is not None:
				expire = int(time.time()) + days * 24 * 3600
		worker = worker[:WORKER_NAME_LEN]
		query = 'INSERT INTO VkTasks (id, worker, ip, down, up, expire) VALUES ({}, "{}", INET_ATON("{}"), {}, {}, FROM_UNIXTIME({}));'
		query = query.format(ind, worker, ip, down, up, expire)
		try:
			self.execute(query)
			return expire
		except MySQLdb.IntegrityError as ex:
			if 'Duplicate entry' in str(ex):
				print('Duplicate task ID-{} of {}@{}'.format(ind, worker, ip))
				res = self.select_task_debt(worker)['expire']
			else:
				raise ex

	def update_task(self, ind, worker, ip, down, up, expire=None, days=None):
		if expire is None:
			if days is not None:
				expire = int(time.time()) + days * 24 * 3600
		worker = worker[:WORKER_NAME_LEN]
		query = """
UPDATE VkTasks
SET worker="{}", ip=INET_ATON("{}"), down={}, up={}, expire=FROM_UNIXTIME({})
WHERE id = {}""".format(worker, ip, down, up, expire, ind)
		self.execute(query)
		return expire

	def select_tasks_count_opened(self):
		query = 'SELECT COUNT(*) AS cnt FROM VkTasks WHERE down < up'
		self.execute(query)
		return self.fetchall()[0][0]

	def select_tasks_opened(self):
		query = 'SELECT id, worker, INET_NTOA(ip), down, up AS cnt, expire FROM VkTasks WHERE down < up ORDER BY worker ASC'
		self.execute(query)
		return self.fetchall()

	def select_workers_count(self):
		# query = 'SELECT COUNT(*) FROM (SELECT worker, ip FROM VkTasks GROUP BY worker, ip) AS t;'
		query = 'SELECT COUNT(DISTINCT worker) AS cnt FROM VkTasks'
		self.execute(query)
		return self.fetchall()[0][0]

	def read_row(self, row, names):
		if len(row) != len(names):
			log_er('- DBVK Error in {}: different row and names len!'.format(whosdaddy()), True)
		res = {}
		for i in range(min(len(row), len(names))):
			if names[i] == 'expire':
				res[names[i]] = int(time.mktime(row[i].timetuple()))
			else:
				res[names[i]] = row[i]
		return res

	def get_stats(self):
		return {
			'users': self.select_user_count(),
			'faces': self.select_faces_count(),
			# 'tasks': self.select_tasks_count_opened(),
			# 'workers': self.select_workers_count(),
			'size': float(self.select_sizes()),
		}


if __name__ == '__main__':
	db = DBVk()

	# db.create_table_tasks()
	# db.create_table_faces()
	# db.create_function()

	# db.insert_task(0, 'aivan', '127.0.0.1', 1, 100, 1540090665)
	# db.update_task(0, 'aivan', '127.0.0.1', 1, 100, 1540147755)
	# print(db.select_task_id(0))
	# print(db.select_task_free())
	# print(db.select_task_new())

	# pi = 3.14159265358979323846264338327950
	# e  = 2.7182818284590452353602874713527
	# name = 'abcd'
	# db.insert_features(0, name, [pi, e])

	# r = db.select_faces()[0]
	# pi2 = r[2]
	# e2 = r[3]
	# d1 = abs(pi2-pi)
	# d2 = abs(e2-e)
	# print('D1: {:.7f}'.format(d1))
	# print('D2: {:.7f}'.format(d2))

	# db.commit_db()

	# print(db.get_stats())
	# print(db.select_tasks_opened())

	# print(db.select_matches([3.15, 2.71]))

