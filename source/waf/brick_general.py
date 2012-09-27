import os

def configure(conf):
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './logfiles'
	if not conf.path.find_dir(conf.env.LOGFILES):
		conf.path.make_node(conf.env.LOGFILES).mkdir()
	os.environ['BRICK_LOGFILES'] = conf.path.make_node(conf.env.LOGFILES).abspath()

	if not conf.env.BRICK_RESULTS:
		conf.env.BRICK_RESULTS = './results'
	if not conf.path.find_dir(conf.env.BRICK_RESULTS):
		conf.path.make_node(conf.env.BRICK_RESULTS).mkdir()
	os.environ['BRICK_RESULTS'] = conf.path.make_node(conf.env.BRICK_RESULTS).abspath()

	if not conf.env.PROJECT_ROOT:
		conf.env.PROJECT_ROOT = '../../'
	if not conf.path.find_dir(conf.env.PROJECT_ROOT):
		conf.path.make_node(conf.env.PROJECT_ROOT).mkdir()
	os.environ['PROJECT_ROOT'] = conf.path.make_node(conf.env.PROJECT_ROOT).abspath()

def build(bld):
	os.environ['BRICK_RESULTS'] = bld.path.make_node(bld.env.BRICK_RESULTS).abspath()
	os.environ['BRICK_LOGFILES'] = bld.path.make_node(bld.env.LOGFILES).abspath()
	os.environ['PROJECT_ROOT'] = bld.path.make_node(bld.env.PROJECT_ROOT).abspath()

