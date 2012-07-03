import os
import subprocess
from Task import Task
from tools.prepare.prepareError import prepareError

class brickContainer:

	# init
	def __init__(self,configFile,configObj):
		self.__config_file = configFile
		self.config = configObj
		self.__preRunHooks = []
		self.__prepareHooks = {}
		self.__state = 'initialized'
		self.__special_sections = ['global','cds_libs','modules']
		self.__tasks = []
	# end of init

	# ----------------------
	#  manage pre_run hooks
	# ----------------------

	def add_pre_run_hook(self,f):
		self.__preRunHooks.append(f)
	# end of add_pre_run_hook

	def print_pre_run_hooks(self):
		for func in self.__preRunHooks:
			print func.__name__
	# end of print_pre_run_hooks

	def run_pre_hooks(self):
		logger.info("Running pre_run_hooks")
		for func in self.__preRunHooks:
			logger.debug("Running pre_run_hook "+func.__name__)
			state = func(self)
			if not state:
				logger.error(" Hook "+func.__name__+" returned "+str(state))
				return False
			else:
				logger.debug(" Hook returned successfully")

		return True
	# end of run_pre_hooks

	# -------------------------
	#  manage task preparation
	# -------------------------

	def generate_tasks(self):
		# iterate over sections in config file
		for sectionName in self.config.sections():
			try:
				# test whether the current section is a special section
				self.__special_sections.index(sectionName)
			except ValueError:
				try:
					# ... if not so, append a task
					self.__tasks.append(Task(self,sectionName,self.config.items(sectionName,False,{'cwd':os.getcwd()})))
				except prepareError, e:
					logger.error("Error in section "+sectionName+": "+e.value)
					return False
		if len(self.__tasks) == 0:
			logger.error('No tasks generated. Probably, you haven\'t defined any tasks in your config file.')
			return False
		else:
			return True

	def add_prepare_hook(self,name,func):
		self.__prepareHooks[name] = func

	def run_prepare_hook(self,name,sectionName,options):
		try:
			return self.__prepareHooks[name](self,sectionName,options)
		except KeyError:
			logger.error('No tool named \''+name+'\' loaded')

	def wscript_configure_method(self):
		wscript_code = """def configure(conf):
		os.environ['RESULTS_DIR'] = '%s'\n""" % (self.get_full_rundir()+'/results')

		return wscript_code

	def prepare_tasks(self):
		# generate Task list
		if not self.generate_tasks():
			return False
		# generate wscript
		f = open(self.get_full_rundir()+'/wscript','w')
		f.write('import os\n')
		f.write('out = "'+self.get_full_rundir()+'/build"\n')
		f.write('top = "'+os.getcwd()+'"\n')
		f.write(self.wscript_configure_method())
		f.write('def build(bld):')
		for task in self.__tasks:
			f.write(task.show_wscript()+"\n")
		f.close()
		# promote state to next level
		self.__state = 'prepared'
		return True

	# -----------------------
	#  manage task execution
	# -----------------------

	def run_tasks(self):
		p = subprocess.Popen('cd '+self.get_full_rundir()+' && waf configure', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		for line in p.stdout:
			print line.rstrip()

		p = subprocess.Popen('cd '+self.get_full_rundir()+' && waf build -v -j1', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		for line in p.stdout:
			print line.rstrip()

		self.__state = 'run'

	# ----------------------------
	#  manage task postprocessing
	# ----------------------------

	def postprocess_tasks(self):
		# do something
		self.__state = 'postprocessed'

	# ------------------
	#  helper functions
	# ------------------

	def get_top_relative_path(self,path):
		if os.path.isabs(path):
			return os.path.normpath(os.path.join('..',os.path.relpath(path,self.get_full_rundir())))
		else:
			return os.path.normpath(os.path.join(os.path.dirname(self.__config_file),path))

	def get_full_path_from_config(self,path):
		if os.path.isabs(path):
			return path
		else:
			if os.path.isabs(os.path.dirname(self.__config_file)):
				return os.path.join(os.path.dirname(self.__config_file),path)
			else:
				return os.path.join(os.getcwd(),os.path.dirname(self.__config_file),path)

	def get_full_rundir(self):
		rundir = self.config.get('global','rundir')
		if os.path.isabs(rundir):
			return rundir
		else:
			if os.path.isabs(os.path.dirname(self.__config_file)):
				return os.path.join(os.path.dirname(self.__config_file),rundir)
			else:
				return os.path.join(os.getcwd(),os.path.dirname(self.__config_file),rundir)

	def check_module_loaded(self,name):
		try:
			existing = [val for (opt,val) in self.config.items('modules') if opt==name][0]
			return True
		except IndexError:
			return False

	def get_option(self,sectionName,optionName,default=None):
		res = [val for (opt,val) in self.config.items(sectionName,False,{'cwd':os.getcwd()}) if opt==optionName]
		if not res:
			# if this fails let the error fall through
			res = [val for (opt,val) in self.config.items('global',False,{'cwd':os.getcwd()}) if opt==optionName]

		if res:
			assert(len(res) == 1)
			return res[0]
		else:
			return default

	# ---------------------
	#  save internal state
	# ---------------------

	def __load_config(self):
		xmlconfig = minidom.parse('./brick_config.xml') # parse an XML file by name
		self.config['projectname'] = brick_waf.getTextNodeValue(xmlconfig,'projectShortName')
		self.config['testcases'] = brick_waf.getTestCases(xmlconfig)

	def get_config_value(self,key):
		return self.config[key]

	# save state to file
	def __save_state(self):
		f = open('./.brick_info','w')
		f.write(self.__rundir+"\n")
		f.write(self.__mode+"\n")
		f.write(self.__testcase+"\n")
		f.write(self.__simulator+"\n")
		f.close()
	# end save state

	# load state from file
	def __load_state(self):
		f = open('./.brick_info','r')
		self.__rundir = f.readline().rstrip()
		self.__mode = f.readline().rstrip()
		self.__testcase = f.readline().rstrip()
		self.__simulator = f.readline().rstrip()
		f.close()
	# end save state

#    # configure
#    def configure(self,mode,rundir,testcase,simulator):
#        # save variables in object fields and give them default values
#        # rundir
#        if not rundir:
#            if not self.__rundir:
#                self.output.append('No rundir was explecitly given. Setting rundir to current datetime string')
#                import datetime
#                jetzt = datetime.datetime.now()
#                self.__rundir=jetzt.strftime("%Y%m%d%H%M")
#        else:
#            self.__rundir = rundir
#        # mode
#        if not mode:
#            if not self.__mode:
#                self.output.append('Please give a mode via the --mode option. Mode can be "build" or "functional"')
#                return
#        else:
#            self.__mode = mode
#        # testcase
#        if testcase:
#            self.__testcase = testcase
#
#        if self.__mode == 'functional' and not self.__testcase:
#            self.output.append("Testcase has to be given in mode 'functional'")
#            return
#        # simulator
#        if not simulator:
#            self.__simulator = 'cadence'
#        else:
#            self.__simulator = simulator
#
#        cmd = ''
#        if self.__mode == 'functional':
#            cmd = './waf configure --mode '+self.__mode+' --out rundirs/'+self.__rundir+" --testcase "+self.__testcase+" --simulator "+self.__simulator
#        else:
#            cmd = './waf configure --mode '+self.__mode+' --out rundirs/'+self.__rundir
#
#        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
#        for line in p.stdout:
#            self.output.append(line.rstrip())
#
#        self.__save_state()
#
#        return
#    # end of configure
#
#    # build
#    def build(self):
#        cmd = './waf build'
#        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
#        for line in p.stdout:
#            self.output.append(line.rstrip())
#        return
#    # end of build
#
#    # run
#    def run(self):
#        cmd = './waf run'
#        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
#        for line in p.stdout:
#            self.output.append(line.rstrip())
#        return
#    # end of run

	def flushOutput(self):
		returnOutput = "\n".join(self.output)
		self.output = []
		return returnOutput

