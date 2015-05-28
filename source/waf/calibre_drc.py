import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context
from brick_general import ChattyBrickTask

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	conf.env['CALIBRE_DRC'] = 'calibre'
	conf.env['CALIBRE_DRV'] = 'calibredrv'
	conf.env['CALIBRE_DRC_OPTIONS'] = [
			'-64', '-hier', '-turbo' ,'-turbo_all',
		]
	conf.env['CALIBRE_DRV_OPTIONS'] = []

@TaskGen.taskgen_method
def get_calibre_drc_rule_file_path(self):
	ret_node = self.bld.bldnode.find_node('calibre_drc_rules')
	if not ret_node:
		ret_node = self.bld.bldnode.make_node('calibre_drc_rules')
		ret_node.mkdir()
	return ret_node


@TaskGen.feature('calibre_drc')
def create_calibre_drc_task(self):

	self.rule_file = self.get_calibre_drc_rule_file_path().make_node('calibre_drc_rules_'+self.name+'_'+self.cellname)

	self.output_file_base = self.get_resultdir_node().make_node(self.cellname)
	self.svdb = self.get_resultdir_node().make_node('svdb')
	if not os.path.exists(self.svdb.abspath()):
		self.svdb.mkdir()

	output = self.output_file_base.change_ext('.drc.results')
	input = [self.layout_gds]

	f = open(self.rule_file.abspath(),"w")
	f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY {1}
LAYOUT SYSTEM GDSII
LAYOUT CASE YES

//LAYOUT RENAME TEXT "/</\\[/g" "/>/\\]/g"

DRC RESULTS DATABASE "{2}.drc.results"
DRC MAXIMUM RESULTS ALL
DRC MAXIMUM VERTEX 4096

DRC CELL NAME NO
DRC SUMMARY REPORT "{2}.drc.summary" REPLACE

VIRTUAL CONNECT COLON NO
VIRTUAL CONNECT REPORT NO

DRC ICSTATION YES

""".format(self.layout_gds.abspath(),self.cellname,self.output_file_base.abspath()))

	if hasattr(self,'unselect_checks') and len(self.unselect_checks)>0:
		f.write('DRC UNSELECT CHECK\n')
		for line in getattr(self,'unselect_checks',[]):
			f.write('\t"'+line+'"\n')

	for inc in self.includes:
		f.write('\nINCLUDE '+inc.abspath())
		input.append(inc)

	f.close()

	t = self.create_task('calibreDrcTask', input, output)

@TaskGen.taskgen_method
def get_calibre_drc_logfile_node(self):
	return self.get_logdir_node().make_node('calibre_drc_'+self.cellname+'.log')

@TaskGen.taskgen_method
def get_calibre_drc_options(self):
	conditional_options = ""
	if hasattr(self,'hcells'):
		conditional_options += ' -hcell '+self.hcells_file.abspath()
	return conditional_options

@Task.always_run
class calibreDrcTask(ChattyBrickTask):
	vars = ['CALIBRE_DRC','CALIBRE_DRC_OPTIONS']
	run_str = '${CALIBRE_DRC} -drc ${gen.get_calibre_drc_options()} ${CALIBRE_DRC_OPTIONS} ${gen.rule_file.abspath()}'

	def check_output(self,ret,out):
		regex = re.compile("--- TOTAL RESULTS GENERATED = ([1-9]\d+)")
		for num,line in enumerate(out.split('\n')):
			match = regex.match(line)
			if match:
				Logs.error("Error in DRC: Found %s errors, for details see %s" % (match.groups(0),self.generator.get_calibre_drc_logfile_node().abspath()))
				ret = 1

		with open(self.generator.get_calibre_drc_logfile_node().abspath(),'w') as f:
			f.write(out)

		return ret


@TaskGen.feature('calibre_rve_drc')
def create_calibre_rve_drc_task(self):
	if not self.report:
		Logs.error('Please name an existing report file for feature \'cds_rve_drc\'')
		return

	try:
		getattr(self,'gds',None).abspath()
	except AttributeError:
		Logs.error('Please name an existing GDSII file for feature \'cds_rve_drc\'')

	t = self.create_task('calibreRveDrcTask', [self.gds, self.report])

@Task.always_run
class calibreRveDrcTask(Task.Task):
	run_str = "${CALIBRE_DRV} -m ${SRC[0].abspath()} -rve -drc ${SRC[1].abspath()}"

# for convenience
@Configure.conf
def calibre_drc(bld,*k,**kw):
	set_features(kw,'calibre_drc')
	return bld(*k,**kw)

# vim: noexpandtab:
