import os, sys, copy
from waflib import TaskGen, Task, Utils, Logs, Errors

def configure(conf):
	# This is interpreted relative to the build path
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	# This is interpreted relative to the build path
	if not conf.env.BRICK_RESULTS:
		conf.env.BRICK_RESULTS = './results'

	conf.env['PROJECT_ROOT'] = conf.srcnode.abspath()
	os.environ['PROJECT_ROOT'] = conf.srcnode.abspath()

def build(bld):
	if not bld.bldnode.find_dir(bld.env.BRICK_RESULTS):
		bld.bldnode.make_node(bld.env.BRICK_RESULTS).mkdir()
	os.environ['BRICK_RESULTS'] = bld.bldnode.make_node(bld.env.BRICK_RESULTS).abspath()

	if not bld.bldnode.find_dir(bld.env.BRICK_LOGFILES):
		bld.bldnode.make_node(bld.env.BRICK_LOGFILES).mkdir()
	os.environ['BRICK_LOGFILES'] = bld.bldnode.make_node(bld.env.BRICK_LOGFILES).abspath()

	os.environ['PROJECT_ROOT'] = bld.srcnode.abspath()

@TaskGen.taskgen_method
def get_logdir_node(self):
	if not self.bld.bldnode.find_dir(self.bld.env.BRICK_LOGFILES):
		self.bld.bldnode.make_node(self.bld.env.BRICK_LOGFILES).mkdir()
	return self.bld.bldnode.make_node(self.bld.env.BRICK_LOGFILES)

from waflib.Configure import conf
from waflib.Errors import WafError
@conf
def convert_string_paths(self,list_of_paths):
	SOURCES = []
	if not type(list_of_paths) == type([]):
		self.fatal('You must give a list of strings as parameter to convert_string_paths')

	for src in list_of_paths:
		if os.path.isabs(src):
			node = self.root.find_node(src)
			if not node:
				node = self.root.make_node(src).get_bld()
				if not node:
					self.fatal('Source file not found: '+src)
			SOURCES.append(node)
		else:
			node = self.path.find_node(src)
			if not node:
				node = self.path.make_node(src).get_bld()
				if not node:
					self.fatal('Source file not found: '+src)
			SOURCES.append(node)

	return SOURCES

class ChattyBrickTask(Task.Task):
	#	# check: https://stackoverflow.com/questions/8980050/persistent-python-subprocess
	def check_output(self, ret, out):
		return ret

	def exec_command(self, cmd, **kw):
		"""
		Combination of TaskBase.exec_command and Context.exec_command with
		modifications to get real-time output from Subprocess.Popen
		"""

		bld = self.generator.bld
		try:
			if not kw.get('cwd', None):
				kw['cwd'] = bld.cwd
		except AttributeError:
			bld.cwd = kw['cwd'] = bld.variant_dir
		#return bld.exec_command(cmd, **kw)

		subprocess = Utils.subprocess
		kw['shell'] = isinstance(cmd, str)
		Logs.debug('runner: %r' % cmd)
		Logs.debug('runner_env: kw=%s' % kw)

		if bld.logger:
			bld.logger.info(cmd)

		# this has been modified
		kw['stdout'] = subprocess.PIPE
		kw['stderr'] = subprocess.STDOUT

		print cmd
		print kw['shell']
		try:
			if kw['stdout'] or kw['stderr']:
				p = subprocess.Popen(cmd, **kw)
				line = p.stdout.readline()
				out = copy.copy(line)
				while line:
					sys.stdout.write(line)
					sys.stdout.flush()
					out += line
					line = p.stdout.readline()
				#(out, err) = p.communicate()
				err = ''
				ret = p.returncode
			else:
				out, err = (None, None)
				ret = subprocess.Popen(cmd, **kw).wait()
		except Exception as e:
			raise Errors.WafError('Execution failure: %s' % str(e), ex=e)

		if out:
			if not isinstance(out, str):
				out = out.decode(sys.stdout.encoding or 'iso8859-1')
			if bld.logger:
				bld.logger.debug('out: %s' % out)
			#else:
			#	sys.stdout.write(out)
		if err:
			if not isinstance(err, str):
				err = err.decode(sys.stdout.encoding or 'iso8859-1')
			if bld.logger:
				bld.logger.error('err: %s' % err)
			#else:
			#	sys.stderr.write(err)

		return self.check_output(ret,out)

# vim: noexpandtab
