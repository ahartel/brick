import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CALIBRE_DRC'] = 'calibre'
	conf.env['CALIBRE_DRV'] = 'calibredrv'
	conf.env['CALIBRE_DRC_OPTIONS'] = [
			'-64', '-hier', '-turbo' ,'-turbo_all',
		]
	conf.env['CALIBRE_DRV_OPTIONS'] = []


@TaskGen.feature('calibre_drc')
def create_calibre_drc_task(self):

	self.rule_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_drc_rules_'+self.cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))
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
	return self.bld.bldnode.find_node(self.env.BRICK_LOGFILES).make_node('calibre_drc_'+self.cellname+'.log')

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
		for num,line in enumerate(out.split('\n')):
			if line.find('ERROR:') == 0:
				Logs.error("Error in line %d: %s" % (num,line[6:]))
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
