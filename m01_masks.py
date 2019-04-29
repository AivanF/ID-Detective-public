# select COUNT(*) AS cnt
# from VkUsers
# where user_id >= 50000000
#   -- and user_id <  70000000
#   and BIT_COUNT(mask) = 0;

from dbvk import *
fs = check_features_names()
db = DBVk()

QSelect = """
SELECT user_id, name, {fs}
FROM VkUsers
WHERE user_id >= {begin}
  AND user_id <  {end}
  AND BIT_COUNT(mask) = 0
"""
QUpdate = 'UPDATE VkUsers SET mask=UNHEX("{mask}") WHERE user_id = {user_id} AND name = "{name}"'

def update_masks(begin, end, limit=-1):
	q = QSelect.format(begin=begin, end=end, fs=fs)
	if limit > 0:
		q += ' LIMIT {}'.format(limit)
	print('Starting from {} to {} | {}'.format(begin, end, limit))
	db.execute(q)
	data = db.fetchall()
	done = 0
	for row in data:
		user_id = row[0]
		name = row[1]
		values = row[2:]
		mask = bit_hash(values).hex()
		# print(user_id, name, mask)
		q = QUpdate.format(mask=mask, user_id=user_id, name=name)
		db.execute(q)
		done += 1
	db.commit_db()
	print('Updated {} rows.'.format(done))

update_masks(70000000, 999000000, 10000)