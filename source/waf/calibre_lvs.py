import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context
from brick_general import ChattyBrickTask

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""
	conf.load('brick_general')

	conf.find_program('calibre',var='CALIBRE_LVS')
	conf.find_program('calibredrv',var='CALIBRE_DRV')

	conf.env['CALIBRE_LVS_OPTIONS'] = [
			'-64', '-hier',
		]

@TaskGen.taskgen_method
def get_calibre_lvs_rule_file_path(self):
	ret_node = self.bld.bldnode.find_node('calibre_lvs_rules')
	if not ret_node:
		ret_node = self.bld.bldnode.make_node('calibre_lvs_rules')
		ret_node.mkdir()
	return ret_node


@TaskGen.feature('calibre_lvs')
def create_calibre_lvs_task(self):

	self.rule_file = self.get_calibre_lvs_rule_file_path().make_node(self.layout_cellname)
	self.hcells_file =  self.get_calibre_lvs_rule_file_path().make_node('calibre_hcells_'+self.layout_cellname)

	self.output_file_base = self.get_resultdir_node().make_node(self.layout_cellname)
	self.svdb = self.get_resultdir_node().make_node('svdb')
	if not os.path.exists(self.svdb.abspath()):
		self.svdb.mkdir()


	f = open(self.rule_file.abspath(),"w")
	f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY {1}
LAYOUT SYSTEM GDSII
LAYOUT CASE YES

//LAYOUT RENAME TEXT "/</\\[/g" "/>/\\]/g"

SOURCE PATH "{2}"
SOURCE PRIMARY "{3}"
SOURCE SYSTEM SPICE
SOURCE CASE YES

MASK SVDB DIRECTORY "{5}" QUERY XRC

LVS REPORT "{4}.lvs.report"

LVS REPORT OPTION A AV B BV C CV D E E1 F FX G H I N O P R RA S V W X
LVS REPORT MAXIMUM ALL

LVS REPORT OPTION NONE
LVS FILTER UNUSED OPTION NONE SOURCE
LVS FILTER UNUSED OPTION NONE LAYOUT

LVS ABORT ON SUPPLY ERROR YES
LVS IGNORE PORTS NO
LVS GLOBALS ARE PORTS NO
VIRTUAL CONNECT REPORT NO
LVS EXECUTE ERC YES
ERC RESULTS DATABASE "sram_row_pst.erc.results"
ERC SUMMARY REPORT "sram_row_pst.erc.summary" REPLACE HIER
ERC MAXIMUM RESULTS 1000
ERC MAXIMUM VERTEX 4096

DRC ICSTATION YES

""".format(self.layout_gds.abspath(),self.layout_cellname,self.source_netlist.abspath(),self.source_cellname,self.output_file_base.abspath(),self.svdb.abspath()))

	for line in getattr(self,'mixins',[]):
		f.write(line+'\n')

	for inc in self.includes:
		f.write('\nINCLUDE '+inc.abspath())

	f.close()

	if hasattr(self,'hcells'):
		f = open(self.hcells_file.abspath(),"w")
		f.write("\n".join(getattr(self,'hcells',[])))
		f.close()

	output = self.svdb.make_node(self.layout_cellname+'.sp')
	open(output.abspath(),'w').close()

	t = self.create_task('calibreLvsTask', [self.layout_gds,self.source_netlist], [self.output_file_base.change_ext(".lvs.report"), output])

@TaskGen.taskgen_method
def get_calibre_lvs_logfile_node(self):
	return self.get_logdir_node().make_node('calibre_lvs_'+self.layout_cellname+'.log')

@TaskGen.taskgen_method
def get_calibre_lvs_spice_node(self):
	return self.svdb.make_node(self.layout_cellname+'.sp')

@TaskGen.taskgen_method
def get_calibre_lvs_options(self):
	conditional_options = ""
	if hasattr(self,'hcells'):
		conditional_options += ' -hcell '+self.hcells_file.abspath()
	return conditional_options

#@Task.always_run
class calibreLvsTask(ChattyBrickTask):
	vars = ['CALIBRE_LVS','CALIBRE_LVS_OPTIONS','CALIBRE_LVS_RULES']
	run_str = '${CALIBRE_LVS} -lvs ${gen.get_calibre_lvs_options()} -spice ${gen.get_calibre_lvs_spice_node().abspath()} ${CALIBRE_LVS_OPTIONS} ${gen.rule_file.abspath()} 2>&1 | tee ${gen.get_calibre_lvs_logfile_node().abspath()}'

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('ERROR:') == 0 or line.find('Error:') == 0:
				Logs.error("Error in line %d: %s" % (num,line[6:]))
				ret = 1
			if line.find('LVS completed. INCORRECT.') == 0:
				Logs.error("Error in line %d: %s" % (num,line))
				ret = 1

		with open(self.generator.get_calibre_lvs_logfile_node().abspath(),'w') as f:
			f.write(out)

		return ret


@TaskGen.feature('calibre_rve_lvs')
def create_calibre_rve_lvs_task(self):
	try:
		getattr(self,'gds',None).abspath()
	except AttributeError:
		Logs.error('Please name an existing GDSII file for feature \'cds_rve_drc\'')

	self.svdb = self.get_resultdir_node().make_node('svdb')
	if not self.svdb:
		Logs.error('Database '+self.get_resultdir_node().make_node('svdb').abspath()+' not found. Please run feature \'calibre_lvs\' first.')

	input = [self.gds]

	t = self.create_task('calibreRveLvsTask',input)

@Task.always_run
class calibreRveLvsTask(Task.Task):
	vars = ['CALIBRE_LVS','CALIBRE_LVS_OPTIONS','CALIBRE_LVS_RULES']
	run_str = "${CALIBRE_DRV} -m ${SRC[0].abspath()} -rve -lvs ${gen.svdb.abspath()} ${gen.cellname}"

# for convenience
@Configure.conf
def calibre_lvs(bld,*k,**kw):
	set_features(kw,'calibre_lvs')
	return bld(*k,**kw)

# vim: noexpandtab:
