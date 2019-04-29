from utils import *


def half1(values):
	return values[:int(len(values) / 2)]
def half2(values):
	return values[int(len(values) / 2):]
def ab_test(values):
	mid = int(len(values) / 2)
	timing_compare(timing_avg(values[:mid]), timing_avg(values[mid:]))


def load_timing(filename):
	with open('time-' + filename + '.txt', 'r') as f:
		data = f.read()
		return [eval(el) for el in data.split('\n') if len(el)>10]


mac = load_timing('aivan')

# Sending to 127.0.0.1
fcom_127 = load_timing('f.com')
fcom = fcom_127
xen3 = fcom

det2 = load_timing('det2')
xen5 = det2

# timing_describe(timing_avg(mac))

# ab_test(mac)
# timing_compare(timing_avg(half1(mac)), timing_avg(half1(fcom)))
# timing_compare(timing_avg(half2(mac)), timing_avg(half2(fcom)))

print('Local Mac vs Remote Server')
timing_compare(timing_avg(mac), timing_avg(fcom))
# print('Local f.com vs det2')
# timing_compare(timing_avg(fcom), timing_avg(det2))

# print('Local fcom-xen3 vs det2-xen5')
# timing_compare(timing_avg(xen3), timing_avg(xen5))
