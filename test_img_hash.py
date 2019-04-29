from os.path import join
from PIL import Image
from test__utils import get_test_photo, get_test_user, all_test_photos, get_test_name


def hash_img(fl):
	img = Image.open(fl)
	img = img.resize((12, 12), Image.ANTIALIAS)
	img = img.convert('L')
	# img.show()
	pixel_data = list(img.getdata())
	avg_pixel = sum(pixel_data) / len(pixel_data)
	bits = "".join(['1' if (px >= avg_pixel) else '0' for px in pixel_data])
	# print(len(bits))
	hex_representation = str(hex(int(bits, 2)))[2:].upper()
	# print(len(hex_representation))
	# print(hex_representation)
	return hex_representation


if __name__ == '__main__':
	for key in all_test_photos():
		fl = get_test_photo(key)
		res = hash_img(fl)
		print(get_test_name(), res)

