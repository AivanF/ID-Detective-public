from utils import *

FEATURES_COUNT = 128
BYTE = 8

d_example_1 = [-0.04255197, 0.09532648, 0.07054815, -0.16549776, -0.12415121, 0.0382191, -0.07312493, -0.09611742, 0.22047682, -0.19801548, 0.15259135, -0.01134261, -0.23963471, 0.01833748, -0.0281624, 0.14097191, -0.23807517, -0.18534157, 0.04293261, -0.06319501, 0.10242895, 0.05262198, 0.02820483, 0.0663024, -0.21452512, -0.32003132, -0.14339951, -0.08019556, -0.03159906, -0.17876017, 0.04818383, 0.0482966, -0.15285429, 0.0771955, -0.08601906, 0.14190909, 0.03086096, -0.162838, 0.14963487, 0.06983525, -0.2949585, -0.06675678, 0.07470582, 0.24171038, 0.2419284, -0.0495593, 0.02699855, -0.03074589, 0.10906073, -0.30742577, 0.06049858, 0.16276181, 0.0315482, 0.10094873, 0.02832384, -0.15352346, 0.04531581, 0.06469844, -0.16872023, -0.0229352, 0.1138309, -0.04570557, 0.12566042, 0.03455648, 0.22692364, 0.10793984, -0.12205909, -0.13853617, 0.15222996, -0.22324964, -0.12466218, 0.08134897, -0.16560642, -0.19175343, -0.28343126, 0.00476735, 0.36970544, 0.19197957, -0.05582938, 0.10238559, -0.1282969, -0.04093469, 0.02137784, 0.20352817, 0.0524757, 0.09660726, -0.11416124, 0.12493343, 0.25468287, -0.06270649, -0.0197041, 0.29399148, 0.01617225, 0.05776942, 0.01948751, 0.13631015, -0.10088278, 0.06212247, -0.10556427, 0.04095189, -0.03144231, 0.02062101, -0.03109386, 0.1667155, -0.18951692, 0.22946598, -0.01217839, -0.07699894, -0.09985337, -0.03250569, -0.04266873, -0.02963913, 0.15991759, -0.26606277, 0.08179519, 0.20901035, 0.0205542, 0.17556855, 0.06139373, 0.0995992, 0.03962972, -0.14156368, -0.18063521, -0.01355247, -0.02652007, -0.03475824, 0.0081715, 0.07981398]
d_dotones = [0.1] * 128
d_zeros = [0.0] * 128

d_sample = [0.0] * 128
for i in range(18):
	d_sample[i] = 0.1

def f_difference(a, b):
	s = 0.0
	for i in range(FEATURES_COUNT):
		s += (a[i] - b[i]) ** 2
	return s ** 0.5

def bit_hash(values):
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

res = bit_hash(d_example_1)
# res = '{0:08b}'.format(res)
print(len(res))
print(res)
print(len(res.hex()))
print(res.hex())


# neg = []
# pos = []
# for el in d_example_1:
# 	if el < 0:
# 		neg.append(el)
# 	if el > 0:
# 		pos.append(el)
# print('Pos. Count: {} Avg: {}'.format(len(pos), sum(pos)/len(pos)))
# print('Neg. Count: {} Avg: {}'.format(len(neg), sum(neg)/len(neg)))


# res = 1.0 - f_difference(d_zeros, d_sample)
# print(res)
# print(str(clamp_percent(res)) + '%')


# https://stackoverflow.com/q/36681373
# https://stackoverflow.com/a/5241478
# https://stackoverflow.com/a/9081348
# https://stackoverflow.com/a/36149089

# https://www.w3resource.com/mysql/string-functions/mysql-unhex-function.php

# SELECT STRCMP('my21', 'my12') AS dif;
# SELECT BIT_COUNT();
# https://dev.mysql.com/doc/refman/8.0/en/bit-functions.html#function_bit-count

query = """
ALTER TABLE VkUsers ADD `mask` BINARY(32) NOT NULL;

SELECT HEX(mask) AS mask, user_id, name FROM VkUsers LIMIT 3;

UPDATE VkUsers
SET mask = UNHEX('00aaaaaaa0000000000000000000000000000000000000000000000000000000')
WHERE user_id = 1;

SELECT BIT_COUNT(UNHEX('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa') & UNHEX('00aaaaaaa0000000000000000000000000000000000000000000000000000000'));
"""