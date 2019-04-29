import time
import atexit
import threading

__timers = {}
__saved_time = {}
__filename = None


def timing_avg(array):
	res = {}
	for this in array:
		for section in this:
			if section not in res:
				res[section] = {}
			cur = this[section]
			curres = res[section]
			for label in cur:
				if label not in curres:
					curres[label] = []
				curres[label].append(cur[label])
	for section in res:
		curres = res[section]
		for label in curres:
			curres[label] = sum(curres[label]) / len(curres[label])
	return res


def timing_describe(values):
	for section in values:
		cur = values[section]
		print('{}:'.format(section))
		for label in cur:
			temp = cur[label]
			print('- {}: {:.4f} sec'.format(label, temp))


def timing_compare(values1, values2):
	for section in values1:
		if section not in values2:
			continue
		cur1 = values1[section]
		cur2 = values2[section]
		sum1, sum2 = 0, 0
		print('{}:'.format(section))
		for label in cur1:
			if label not in cur1:
				continue
			temp1 = cur1[label]
			temp2 = cur2[label]
			# TODO: calc percent?
			print('- {}: {:.3f} vs {:.3f} (dif {:.3f})'.format(label, temp1, temp2, temp2-temp1))
			sum1 += temp1
			sum2 += temp2
		print('- sum: {:.3f} vs {:.3f} (dif {:.3f})'.format(sum1, sum2, sum2-sum1))


def tick(section='', label=None):
	newtime = time.time()
	the_name = threading.current_thread().name
	if the_name not in __saved_time:
		__saved_time[the_name] = {}
	saved_time = __saved_time[the_name]

	if label is not None:
		if section not in __timers:
			__timers[section] = {}
		cur = __timers[section]
		if label not in cur:
			cur[label] = []
		if len(cur[label]) < 200 and section in saved_time:
			cur[label].append(newtime - saved_time[section])
	saved_time[section] = newtime


def tock(pretty=True):
	global __timers, __saved_time
	if len(__timers) == 0:
		return
	res = {}
	for section in __timers:
		cur = __timers[section]
		curres = {}
		for label in cur:
			temp = cur[label]
			if len(temp) > 0:
				curres[label] = sum(temp) / len(temp)
		res[section] = curres
	__timers = {}
	__saved_time = {}
	if pretty:
		timing_describe(res)
	if __filename is not None:
		with open(__filename, 'a') as f:
			f.write(str(res) + '\n')
	return res


def set_timer_file(filename):
	global __filename
	__filename = filename


class Progress(object):
	def __init__(self, total, initial=0, change=5, autoshow=False, key=''):
		self.total = total
		self.current = initial
		self.last = int(100.0 * initial / total)
		self.change = change
		self.notes = {}
		self.key = key

		def callback():
			self.show_notes()

		if autoshow:
			atexit.register(callback)

	def add(self, count=1):
		self.current += count
		cur = int(100.0 * self.current / self.total)
		if cur - self.last >= self.change or self.current == self.total:
			self.last = cur
			print('Progress {}%'.format(cur))

	def note(self, label, key=None):
		if key is not None:
			if key == True:
				label = '[{}] {}'.format(self.key, label)
			else:
				label = '[{}] {}'.format(key, label)
		if label not in self.notes:
			self.notes[label] = 1
		else:
			self.notes[label] += 1

	def show_notes(self):
		if len(self.notes) > 0:
			print('Notes:')
			for label in self.notes:
				print('- {}: {} ({}%)'.format(label, self.notes[label], int(100.0 * self.notes[label] / self.total)))

