from .notes import set_timer_file, timing_avg, timing_describe, timing_compare, tick, tock, Progress
from .decor import multi_first, multi_all, obj_multi_first, obj_multi_all
from .files import read_json, save_json, find_filenames, bio_download, bio_download_named, bio_save, load_pickle, save_pickle
from .logger import setup_logger, log_inf, log_er, log_ex, whoami, whosdaddy
from .singleton import SingleInstance


def debugit(value, comment=None):
	txt = '\t[ '
	if comment is None:
		txt += 'DEBUG IT ]'
	else:
		txt += comment + ' ]'
	txt += '\n- Type: ' + str(type(value))
	txt += '\n- Value:' + str(value)
	print(txt + '\n')
	return txt


def clamp_percent(value, mn=45, mx=70):
	value = 100.0 * value
	value -= mn
	value *= 100.0 / (mx - mn)
	value = int(value)
	value = max(0, min(99, value))
	return value


def incr(d, key):
	if key not in d:
		d[key] = 1
	else:
		d[key] += 1


def dsum(core, addition):
	# Adds numbers from one dict to another
	for key in addition:
		if key in core:
			core[key] += addition[key]
		else:
			core[key] = addition[key]


def isiter(obj):
	# try:
	# 	obj_iterator = iter(obj)
	# 	return True
	# except TypeError as te:
	# 	return False
	return isinstance(obj, list) or isinstance(obj, tuple) or isinstance(obj, set)


def dfind(obj, target, value=None):
	for key in obj:
		if target in key:
			return obj[key]
	return value


def dfindsum(obj, targets):
	res = 0
	if not isiter(targets):
		targets = [targets]
	for key in obj:
		matched = False
		for part in targets:
			if part in key:
				matched = True
				break
		if matched:
			res += obj[key]
	return res
