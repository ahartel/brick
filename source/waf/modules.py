import os, subprocess, time, re
from waflib.Configure import conf

def configure(conf):
	conf.start_msg('Checking for program module')
	# this does not work, since module is a exported as a function on valgol:
	# conf.find_program('module')
	# Therfore:
	if os.system('module purge') == 0:
		conf.end_msg('module')
	else:
		conf.end_msg('module not found')
		conf.fatal('Could not find the program module')

@conf
def load_modules(self,*k,**kw):
	module_string = ''
	try:
		for module in kw['modules']:
			module_string += module+' '
	except KeyError:
		self.fatal('You must give modules to function check_modules like this: check_module(modules=[a,b,c])')

	#self.start_msg('Loading modules')

	p = subprocess.Popen('bash /usr/local/Modules/current/init/bash && module load '+module_string+' && export -p', shell=True, stdout=subprocess.PIPE)
	p.wait()

	if p.returncode == 0:
		for key in os.environ.iterkeys():
			os.unsetenv(key)

		for line in p.stdout:
			m = re.search('(\w+)=(".+")$', line)
			if (m):
				os.putenv(m.group(1), m.group(2))

		#self.end_msg(module_string)
	else:
		self.fatal('Loading modules did not work')
