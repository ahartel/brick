import os

def configure(conf):
	# This is interpreted relative to the build path
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	# This is interpreted relative to the build path
	if not conf.env.BRICK_RESULTS:
		conf.env.BRICK_RESULTS = './results'

	if not conf.env.PROJECT_ROOT:
		conf.env.PROJECT_ROOT = '../../'
	if not conf.path.find_dir(conf.env.PROJECT_ROOT):
		conf.path.make_node(conf.env.PROJECT_ROOT).mkdir()
	os.environ['PROJECT_ROOT'] = conf.path.make_node(conf.env.PROJECT_ROOT).abspath()

def build(bld):
	if not bld.bldnode.find_dir(bld.env.BRICK_RESULTS):
		bld.bldnode.make_node(bld.env.BRICK_RESULTS).mkdir()
	os.environ['BRICK_RESULTS'] = bld.bldnode.make_node(bld.env.BRICK_RESULTS).abspath()

	if not bld.bldnode.find_dir(bld.env.BRICK_LOGFILES):
		bld.bldnode.make_node(bld.env.BRICK_LOGFILES).mkdir()
	os.environ['BRICK_LOGFILES'] = bld.bldnode.make_node(bld.env.LOGFILES).abspath()
	os.environ['PROJECT_ROOT'] = bld.path.make_node(bld.env.PROJECT_ROOT).abspath()


from waflib.Configure import conf
from waflib.Errors import WafError
@conf
def convert_string_paths(self,list_of_paths):
	SOURCES = []
	if not type(list_of_paths) == type([]):
		self.fatal('You must give a list of strings as parameter to convert_string_paths')

	for src in list_of_paths:
		if not os.path.exists(src):
			raise WafError('File '+src+' not found in function \'convert_string_paths\'.')
		if os.path.isabs(src):
			SOURCES.append(self.root.find_node(src))
		else:
			SOURCES.append(self.path.find_node(src))

	return SOURCES
