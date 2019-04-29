import sys, traceback
from os import getcwd
from os.path import join
import inspect
import logging
import atexit


def whoami():
	return inspect.stack()[1][3]


def whosdaddy():
	return inspect.stack()[2][3]


__logger = None
__exceptions = 0
__errors = 0
__infos = 0


def setup_logger(name):
	global __logger
	__logger = logging.getLogger('my_special')
	__logger.setLevel(logging.INFO)
	# dir_path = os.path.dirname(os.path.realpath(__file__))
	path = join(getcwd(), 'Logs/log-{}.html'.format(name))
	fh = logging.FileHandler(path, encoding='utf-8')
	html_format = '<h3>%(module)s – %(levelname)s – %(asctime)s:</h3>%(message)s<br><br>'
	html_format = logging.Formatter(html_format)
	fh.setFormatter(html_format)
	__logger.addHandler(fh)


def __exiter():
	if __infos > 0:
		print('\tInfo: {}'.format(__infos))
	if __errors > 0:
		print('\tErrors: {}'.format(__errors))
	if __exceptions > 0:
		print('\tExceptions: {}'.format(__exceptions))


atexit.register(__exiter)


def log_inf(text, show=False):
	global __infos
	__infos += 1
	if __logger is not None:
		__logger.info(text)
	else:
		print('\n\tLogger was not created!\n')
	if show:
		print(text)


def log_er(text, show=False):
	global __errors
	__errors += 1
	if __logger is not None:
		__logger.error(text)
	else:
		print('\n\tLogger was not created!\n')
	if show:
		print(text)


def log_ex(ex, comment=None, show=False):
	global __exceptions
	__exceptions += 1
	etype, value, tb = sys.exc_info()
	tr = traceback.format_exception(etype, value, tb)
	tr = ''.join(tr)
	res = 'Execution error!\n' + tr
	if comment:
		res += '\nAdditional info:\n' + str(comment)

	print(res)
	res = res.replace('\n', '\n<br>')
	if __logger is not None:
		__logger.error(res)
	else:
		print('\n\tLogger was not created!\n')
	
