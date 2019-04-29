from utils import *

can_install = False

# name = 'fcom'
# name = 'det2'
name = 'detm'

hosts = read_config()
access = hosts[name]['access']
con = PrettySSH(show_cmd=0, show_out=0, **access)

# con.exec_cd('/aivanf/ID-det')
# print(con.exec_pwd())
# con.exec_rmdir("'lol ahah'")
# print(con.exec_ls())

# print(con.execute_parse('cat /proc/swaps'))
# print(con.execute_parse("grep 'Swap' /proc/meminfo"))

# print(con.get_results())

if can_install:
	con.execute_parse('sudo apt-get update', show_cmd=True)
	con.say_good('apt-get update done.')

if not con.exec_isfound('git --version'):
	con.say_bad('No GIT!')
	if can_install:
		con.execute_parse('sudo apt-get install git-core -y')
		con.say_good('Installed GIT!')
else:
	con.say_good('GIT is installed')

if not con.exec_isfound('make --version'):
	con.say_bad('No Make!')
	if can_install:
		con.execute_parse('sudo apt-get install build-essential')
		con.say_good('Installed Make within build-essential!')
else:
	con.say_good('Make is installed')

if not con.exec_isfound('cmake --version'):
	con.say_bad('No CMake!')
	if can_install:
		con.execute_parse('sudo apt-get install cmake -y')
		con.say_good('Installed CMake!')
else:
	con.say_good('CMake is installed')

checker = False
if insublist(con.execute_parse('mysql -V'), 'Ver 8', 0):
	con.say_good('MySQL 8 is installed')
	checker = True
else:
	if con.exec_isfound('mysql -V'):
		con.say_bad('Other MySQL version is installed!')
	else:
		con.say_bad('No MySQL 8!')
if checker:
	if not con.exec_isfound('mysql_config -V'):
		con.say_bad('No mysql_config!')
		if can_install:
			con.execute_parse('sudo apt-get install libmysqlclient-dev')
			con.say_good('Installed mysql_config!')
	else:
		con.say_good('mysql_config is installed')

if con.exec_isfound('nginx -V'):
	con.say_good('NginX 8 is installed')
else:
	con.say_bad('No NginX!')

if not con.exec_isfound('python2 -V'):
	con.say_bad('No python2!')
else:
	con.say_good('python2 is installed')

if not con.exec_isfound('python3 -V'):
	con.say_bad('No python3!')
	if can_install:
		con.execute_parse('sudo apt-get install python3.6 -y')
		con.say_good('Installed python3!')
else:
	con.say_good('python3 is installed')

if not con.exec_isfound('pip3 -V'):
	con.say_bad('No pip3!')
	if can_install:
		con.execute_parse('sudo apt-get install python3-pip -y')
		con.say_good('Installed pip3!')
else:
	con.say_good('pip3 is installed')


checker = False
if insublist(con.execute_parse('gcc-7 --version'), ' 7', 0):
	con.say_good('gcc-7 is installed')
	checker = True
else:
	con.say_bad('No gcc-7!')
	if can_install:
		con.say_neutral('Installing...')
		con.execute_parse('apt install gcc-7', show_out=True)
		con.say_good('Installed gcc!')
		checker = True
if checker:
	if insublist(con.execute_parse('gcc --version'), ' 7', 0):
		con.say_good('gcc is linked with gcc-7')
	else:
		con.say_bad('gcc is NOT linked with gcc-7!')
		print(con.execute_parse('sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 50'))
		con.say_good('Linked gcc-7!')

checker = False
if insublist(con.execute_parse('g++-7 --version'), ' 7', 0):
	con.say_good('g++-7 is installed')
	checker = True
else:
	con.say_bad('No g++-7!')
	if can_install:
		con.say_neutral('Installing...')
		con.execute_parse('apt install g++-7', show_out=True)
		con.say_good('Installed g++!')
		checker = True
if checker:
	if insublist(con.execute_parse('g++ --version'), ' 7', 0):
		con.say_good('g++ is linked with g++-7')
	else:
		con.say_bad('g++ is NOT linked with g++-7!')
		print(con.execute_parse('sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-7 50'))
		con.say_good('Linked g++-7!')


# pip3 install setuptools
# sudo apt-get install python3-dev
# sudo apt-get install libssl-dev


# if can_install:
# 	con.execute_parse('mkdir /aivanf ; cd /aivanf ; git clone https://github.com/davisking/dlib.git', show_cmd=True, show_out=True)
# 	con.execute_parse('cd /aivanf/dlib ; python3 setup.py install', show_cmd=True, show_out=True)
# 	con.say_neutral('Done')


have_modules = con.pip_list('pip3')
# print('Have pip3 modules: {}'.format(have_modules))
need_modules = ['requests', 'face_recognition', 'flask', 'mysqlclient']
for cur in need_modules:
	if cur in have_modules:
		con.say_good('(pip3) {} is installed'.format(cur))
	else:
		con.say_bad('No (pip3) {} !'.format(cur))
		if can_install:
			if con.pip_install(cur, 'pip3', show_cmd=True, show_out=False):
				con.say_good('Installed (pip3) {} !'.format(cur))
			else:
				con.say_bad('Failed to install (pip3) {} !'.format(cur))



# print(con.execute_parse('pip3 -V'))
# print(con.get_results())
# print(con.execute_parse('pwd'))
