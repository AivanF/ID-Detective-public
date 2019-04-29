
def multi_first(func):
	def wrapper(first, *args, **kwargs):
		if isinstance(first, list) or isinstance(first, tuple):
			return [func(x, *args, **kwargs) for x in first]
		else:
			return func(first, *args, **kwargs)
	return wrapper


def multi_all(func):
	def wrapper(*args, **kwargs):
		if len(args) == 1:
			first = args[0]
			if isinstance(first, list) or isinstance(first, tuple):
				return [func(x, **kwargs) for x in first]
			else:
				return func(first, **kwargs)
		else:
			return [func(x, **kwargs) for x in args]
	return wrapper


def obj_multi_first(func):
	# Skips first argument – self
	def wrapper(self, first, *args, **kwargs):
		if isinstance(first, list) or isinstance(first, tuple):
			return [func(self, x, *args, **kwargs) for x in first]
		else:
			return func(self, first, *args, **kwargs)
	return wrapper


def obj_multi_all(func):
	# Skips first argument – self
	def wrapper(self, *args, **kwargs):
		if len(args) == 1:
			first = args[0]
			if isinstance(first, list) or isinstance(first, tuple):
				return [func(self, x, **kwargs) for x in first]
			else:
				return func(self, first, **kwargs)
		else:
			return [func(self, x, **kwargs) for x in args]
	return wrapper


class Tester():
	def __init__(self, initial):
		self.initial = initial

	@obj_multi_first
	def process(self, value):
		return value * self.initial


if __name__ == '__main__':
	t = Tester(3)
	res = t.process([2, 3, 8, 1])
	print(res)
