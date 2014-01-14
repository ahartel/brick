import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CDS_STRMOUT'] = 'strmout'
	conf.env['CDS_STRMOUT_OPTIONS'] = [
			'-snapToGrid',
			'-case', 'preserve'
		]

@TaskGen.feature('cds_strmout')
def create_cds_strmout_task(self):
	try:
		cellview = getattr(self,'cellview','')
		if cellview.find('.') == -1 or cellview.find(':') == -1:
			Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_strmout\'.')
			return
		(self.libname,rest) = cellview.split(".")
		(self.cellname,self.viewname) = rest.split(":")
		try:
			layout_node = self.get_cellview_path(cellview,True).make_node('layout.oa')
		except AttributeError:
			Logs.error("Cellview '"+cellview+"' not found in path "+self.get_cellview_path(cellview))
			return

		results_dir = self.path.get_bld().make_node('results')
		if not os.path.exists(results_dir.abspath()):
			results_dir.mkdir()

		strmfile = getattr(self,'strmfile', results_dir.make_node(self.libname+'_'+self.cellname+'.gds'))

		t = self.create_task('cdsStrmoutTask', layout_node, strmfile)
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_strmout", you need to specify a parameter "view" in the form of lib.cell:view')


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

# vim: noexpandtab
