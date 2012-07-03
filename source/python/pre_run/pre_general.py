from preRunHook import preRunHook
import os
import ConfigParser

@preRunHook
def general_prerun_hook(brick):
	try:
		rundir = brick.get_full_rundir()
	except ConfigParser.NoSectionError:
		logger.error('No section named \'global\' in config file. Most probably, you haven\'t specified a config file')
		return False
	# generate rundir
	if not os.path.isdir(rundir):
		os.mkdir(rundir)
	# generate logfile dir
	if not os.path.isdir(rundir+'/logfiles'):
		os.mkdir(rundir+'/logfiles')
	# generate results dir
	if not os.path.isdir(rundir+'/results'):
		os.mkdir(rundir+'/results')
	# generate waf build dir
	if not os.path.isdir(rundir+'/build'):
		os.mkdir(rundir+'/build')

	return True
