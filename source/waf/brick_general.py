import os

def configure(conf):
	# This is interpreted relative to the build path
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	# This is interpreted relative to the build path
	if not conf.env.BRICK_RESULTS:
		conf.env.BRICK_RESULTS = './results'


def build(bld):
	if not bld.bldnode.find_dir(bld.env.BRICK_RESULTS):
		bld.bldnode.make_node(bld.env.BRICK_RESULTS).mkdir()
	os.environ['BRICK_RESULTS'] = bld.bldnode.make_node(bld.env.BRICK_RESULTS).abspath()

	if not bld.bldnode.find_dir(bld.env.BRICK_LOGFILES):
		bld.bldnode.make_node(bld.env.BRICK_LOGFILES).mkdir()
	os.environ['BRICK_LOGFILES'] = bld.bldnode.make_node(bld.env.BRICK_LOGFILES).abspath()


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

# vim: noexpandtab
