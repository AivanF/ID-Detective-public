import json


def debugit(val, comment=None):
	txt = '\t[ '
	if comment is None:
		txt += 'DEBUG IT ]'
	else:
		txt += comment + ' ]'
	txt += '\n- Type: ' + str(type(val))
	txt += '\n- Value:' + str(val)
	print(txt + '\n')
	return txt


def insublist(values, sub, index):
	if len(values) > index:
		return sub in values[index]
	else:
		return False


def read_config():
	with open('hosts.json', 'r') as f:
		return json.loads(f.read())