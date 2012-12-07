import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CALIBRE_PEX'] = 'calibre'
	if not conf.env.CALIBRE_PEX_OPTIONS:
		conf.env['CALIBRE_PEX_OPT_PHDB'] = [
			'-64', '-turbo',
		]
		conf.env['CALIBRE_PEX_OPT_PDB'] = [
			'-64', '-turbo', '-rcc',
		]
		conf.env['CALIBRE_PEX_OPT_FMT'] = [
			'-64',
		]
		conf.env['CALIBRE_PEX_OPT_LVS'] = [
			'-64', '-turbo',
		]



@TaskGen.feature('calibre_pex')
def create_calibre_pex_task(self):

	self.rule_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_pex_rules_'+self.cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))

	f = open(self.rule_file.abspath(),"w")
	try:
		f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY "{1}"
LAYOUT SYSTEM GDSII
LAYOUT CASE YES

SOURCE PATH "{2}"
SOURCE PRIMARY "{3}"
SOURCE SYSTEM SPICE
SOURCE CASE YES

MASK SVDB DIRECTORY "{5}" QUERY XRC CCI NOPINLOC IXF NXF SLPH

LVS REPORT "{4}.lvs.report"

PEX NETLIST "{4}.pex.netlist" HSPICE 1 SOURCENAMES GROUND "gnd" LOCATION RCNAMED RLOCATION RWIDTH RLENGTH RLAYER RTHICKNESS 
PEX REPORT "{4}.pex.report" SOURCENAMES
PEX EXTRACT INCLUDE SOURCENAMES TOPLEVEL "{6}"
PEX REDUCE ANALOG NO
PEX REDUCE MINCAP COMBINE 0.001
PEX REDUCE MINCAP REMOVE 0
PEX REDUCE MINRES COMBINE 0.1
PEX REDUCE MINRES SHORT 0
PEX NETLIST UPPERCASE KEYWORDS NO
PEX NETLIST VIRTUAL CONNECT NO
PEX NETLIST NOXREF NET NAMES NO
PEX NETLIST MUTUAL RESISTANCE YES


LVS REPORT OPTION NONE
LVS FILTER UNUSED OPTION AG RC RE RG SOURCE
LVS FILTER UNUSED OPTION AG RC RE RG LAYOUT

LVS RECOGNIZE GATES NONE

DRC ICSTATION YES

LVS POWER NAME
"vdd"
"vdd12a"
"vdd12d"
"vdd25a"
"vdd25d"
"vdd"
LVS GROUND NAME
"gnd"
"gnda"
"gndd"
"gnd"
		""".format(self.layout_gds.abspath(),self.cellname,self.source_netlist.abspath(),self.cellname,self.output_file_base.abspath(),self.svdb.abspath(),'" "'.join(getattr(self,'only_extract_nets',[]))))

	except AttributeError as e:
		error_string = str(e)
		error_string = error_string.replace('\'task_gen\' object has no','')
		Logs.error('Please specify the missing parameter in the task generator call for feature calibre_pex: '+error_string)
		return

	for inc in self.includes:
		f.write('\nINCLUDE "'+inc.abspath()+'"')

	#for line in getattr(self,'mixins',[]):
	#	f.write('\n'+line)

	f.close()

	t = self.create_task('calibrePexTask', [self.layout_gds,self.source_netlist], self.output_file_base.change_ext(".pex.netlist"))


class calibrePexTask(Task.Task):
	vars = ['CALIBRE_PEX','CALIBRE_PEX_OPT_LVS','CALIBRE_PEX_OPT_PDB','CALIBRE_PEX_OPT_FMT']

	def run_pex(self,stepname):
		conditional_options = ""
		if hasattr(self.generator,'only_extract_nets') and stepname == 'pdb':
			conditional_options += ' -select'
		run_str = '%s -xrc -%s %s %s %s' % (self.env.CALIBRE_PEX, stepname, conditional_options," ".join(self.env['CALIBRE_PEX_OPT_'+stepname.upper()]), self.generator.rule_file.abspath())

		out = ""

		try:
			out = self.generator.bld.cmd_and_log(run_str)
		except Exception as e:
			out = e.stdout + e.stderr

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_pex_'+stepname+'_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

	def run_lvs(self):
		run_str = '%s -lvs -hier -spice %s %s %s' % (self.env.CALIBRE_PEX, self.generator.svdb.make_node(self.generator.cellname+'.sp').abspath(), " ".join(self.env['CALIBRE_PEX_OPT_LVS']), self.generator.rule_file.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)
		except Exception as e:
			out = e.stdout + e.stderr

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_pex_lvs_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

	def run(self):
		# phdb
		#self.run_pex('phdb')
		self.run_lvs()
		# pdb
		self.run_pex('pdb')
		# fmt
		self.run_pex('fmt')

		return 0


# for convenience
@Configure.conf
def calibre_pex(bld,*k,**kw):
	set_features(kw,'calibre_pex')
	return bld(*k,**kw)


