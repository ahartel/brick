import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CALIBRE_LVS'] = 'calibre'
	conf.env['CALIBRE_LVS_OPTIONS'] = [
			'-64', '-hier',
		]


@TaskGen.feature('calibre_lvs')
def create_calibre_lvs_task(self):

	self.rule_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_lvs_rules_'+self.layout_cellname))
	self.hcells_file =  self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_hcells_'+self.layout_cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.layout_cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))
	if not os.path.exists(self.svdb.abspath()):
		self.svdb.mkdir()

	recognize_gates = getattr(self,'recognize_gates','NONE')
	if recognize_gates == True:
		recognize_gates = 'ALL'

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

DRC ICSTATION YES

LVS REPORT OPTION NONE
LVS FILTER UNUSED OPTION NONE SOURCE
LVS FILTER UNUSED OPTION NONE LAYOUT

LVS RECOGNIZE GATES {6}
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

""".format(self.layout_gds.abspath(),self.layout_cellname,self.source_netlist.abspath(),self.source_cellname,self.output_file_base.abspath(),self.svdb.abspath(),recognize_gates))

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
	return self.bld.bldnode.find_node(self.env.BRICK_LOGFILES).make_node('calibre_lvs_'+self.layout_cellname+'.log')

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
	if not self.svdb:
		Logs.error('Please name an existing svdb directory for feature \'cds_rve_lvs\'')
		return

	spice_file = self.svdb.find_node(self.cellname+'.sp')

	t = self.create_task('calibreRveLvsTask',spice_file)

@Task.always_run
class calibreRveLvsTask(Task.Task):
	vars = ['CALIBRE_LVS','CALIBRE_LVS_OPTIONS','CALIBRE_LVS_RULES']
	def run(self):
		run_str = "%s -rve -lvs %s %s" % (self.env.CALIBRE_LVS, self.generator.svdb.abspath(),self.generator.cellname)
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout


# for convenience
@Configure.conf
def calibre_lvs(bld,*k,**kw):
	set_features(kw,'calibre_lvs')
	return bld(*k,**kw)

# vim: noexpandtab:
