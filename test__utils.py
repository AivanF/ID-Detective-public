from os.path import join

TEST_PHOTOS = (
	('kml.jpg', 140795851), # 0 threshold must be 50
	('summer.jpg', 172554877), # 1 threshold must be 46
	('alwhap.jpg', 172554877), # 2 threshold must be 48
	('mhil.jpg', 185228127), # 3
	('aralex.jpg', 50416034), # 4
)
USED_INDEX = [-1]


def get_test_photo(checker=None):
	needed = -1
	if isinstance(checker, str):
		for i, obj in enumerate(TEST_PHOTOS):
			if checker in obj[0]:
				needed = i
				break
		if needed == -1:
			raise Exception('Key "{}" was not found!'.format(checker))
	elif isinstance(checker, int):
		needed = checker % len(TEST_PHOTOS)
	else:
		needed = 0

	filename = TEST_PHOTOS[needed][0]
	USED_INDEX[0] = needed
	path = '/.../TestPhotos'
	return open(join(path, filename),'rb')

def get_test_user():
	return TEST_PHOTOS[USED_INDEX[0]][1]

def get_test_name():
	return TEST_PHOTOS[USED_INDEX[0]][0]

def all_test_photos():
	return range(len(TEST_PHOTOS))


if __name__ == '__main__':
	get_test_photo()
	assert get_test_user() == TEST_PHOTOS[0][1]
	get_test_photo('what')
	assert get_test_user() == TEST_PHOTOS[2][1]
	get_test_photo(3)
	assert get_test_user() == TEST_PHOTOS[3][1]
	print('Tested all!')
