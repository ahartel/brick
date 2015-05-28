import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('cadence_base')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	conf.find_program('strmout', var='CDS_STRMOUT')
	conf.env['CDS_STRMOUT_OPTIONS'] = [
			'-snapToGrid',
			'-case', 'preserve'
		]

@TaskGen.feature('cds_strmout')
def create_cds_strmout_task(self):
	try:
		layout_node = self.get_cellview_path(self.cellview,True).make_node('layout.oa')
	except AttributeError:
		Logs.error("Cellview '"+cellview+"' not found in path "+self.get_cellview_path(cellview))
		return 1
	except ValueError:
		Logs.Error('For feature "cds_strmout", you need to specify a parameter "cellview" in the form of lib.cell:view')
		return 1

	t = self.create_task('cdsStrmoutTask', layout_node, self.get_cadence_strmout_gds_node())

@TaskGen.taskgen_method
def get_cadence_strmout_gds_node(self):
	lib,cell,view = self.get_cadence_lib_cell_view_from_cellview()
	return getattr(self,'strmfile', self.get_cadence_strmout_results_dir().make_node(lib+'_'+cell+'.gds'))

@TaskGen.taskgen_method
def get_cadence_strmout_results_dir(self):
	return self.get_resultdir_node()

class cdsStrmoutTask(ChattyBrickTask):
	vars = ['CDS_STRMOUT']
	run_str = '${CDS_STRMOUT} -library ${gen.get_cadence_lib_cell_view_from_cellview()[0]} -topcell ${gen.get_cadence_lib_cell_view_from_cellview()[1]} -view ${gen.get_cadence_lib_cell_view_from_cellview()[2]} ${CDS_STRMOUT_OPTIONS} -strmfile ${TGT[0].abspath()}'


# for convenience
@Configure.conf
def cds_strmout(bld,*k,**kw):
	set_features(kw,'cds_strmout')
	return bld(*k,**kw)

# vim: noexpandtab
