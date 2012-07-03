from preRunHook import preRunHook
import os
import ConfigParser

@preRunHook
def cadence_prerun_hook(brick):
	# It is necessary to run this module only if cadence tools are used
	# This is usually indicated by the cds_libs section
	try:
		# looking for section cds_libs in config file
		brick.config.items('cds_libs',True)
	except ConfigParser.NoSectionError:
		logger.debug("Not creating cadence run files. Seems to be unnecessary. Create cds_libs section in config file to force creation of these files.")
		return True

	rundir = brick.get_full_rundir()
	# generate hdl.var
	f = open(rundir+'/hdl.var','w')
	f.write('DEFINE WORK worklib\n')
	f.close()
	# create worklib
	if not os.path.isdir(rundir+'/worklib/'):
		os.mkdir(rundir+'/worklib/')
	# generate cds.lib
	f = open(rundir+'/cds.lib','w')
	f.write('DEFINE worklib '+rundir+'/worklib\n')
	for option in brick.config.options('cds_libs'):
		path = brick.config.get('cds_libs',option,False,{'cwd':os.getcwd()})
		f.write('DEFINE '+option+' '+path+'\n')
	f.close()

	return True
