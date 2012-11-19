import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './'
	conf.env['CDS_STRMOUT'] = 'strmout'
	conf.env['CDS_STRMOUT_OPTIONS'] = [
			'-snapToGrid',
			'-case', 'lower'
		]

@TaskGen.feature('cds_strmout')
def create_cds_strmout_task(self):
	try:
		cellview = getattr(self,'view','')
		if cellview.find('.') == -1 or cellview.find(':') == -1:
			Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_strmout\'.')
			return
		(self.libname,rest) = cellview.split(".")
		(self.cellname,self.viewname) = rest.split(":")

		t = self.create_task('cdsStrmoutTask', None,getattr(self,'strmfile',None))
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_strmout", you need to specify a parameter "view" in the form of lib.cell:view')


@Task.always_run
class cdsStrmoutTask(Task.Task):
	vars = ['CDS_STRMOUT']

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = '${CDS_STRMOUT} -library '+self.generator.libname+' -topcell '+self.generator.cellname+' -view '+self.generator.viewname+' ${CDS_STRMOUT_OPTIONS} -strmfile ${TGT[0].abspath()}'

		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)



# for convenience
@Configure.conf
def cds_strmout(bld,*k,**kw):
	set_features(kw,'cds_strmout')
	return bld(*k,**kw)


