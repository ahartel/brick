import os

def configure(conf):
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './logfiles'
	if not conf.path.find_dir(conf.env.LOGFILES):
		conf.path.make_node(conf.env.LOGFILES).mkdir()
	os.environ['BRICK_LOGFILES'] = conf.path.make_node(conf.env.LOGFILES).abspath()
	#os.environ['BRICK_LOGFILES'] = conf.env.LOGFILES

	if not conf.env.BRICK_RESULTS:
		conf.env.BRICK_RESULTS = './results'
	if not conf.path.find_dir(conf.env.BRICK_RESULTS):
		conf.path.make_node(conf.env.BRICK_RESULTS).mkdir()
	os.environ['BRICK_RESULTS'] = conf.path.make_node(conf.env.BRICK_RESULTS).abspath()
	#os.environ['BRICK_RESULTS'] = conf.env.RESULTS_DIR

