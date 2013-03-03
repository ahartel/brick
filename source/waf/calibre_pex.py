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
	self.xcells_file =  self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_xcells_'+self.cellname))
	self.hcells_file =  self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_hcells_'+self.cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))

	which_names = 'LAYOUTNAMES'
	if hasattr(self,'source_netlist'):
		which_names = 'SOURCENAMES'

	selected_nets = ""
	if hasattr(self,'only_extract_nets') and len(self.only_extract_nets) > 0:
		include_mode = 'TOPLEVEL'
		if getattr(self,'extract_include_recursive',False):
			include_mode = 'RECURSIVE'

		selected_nets = 'PEX EXTRACT INCLUDE '+which_names+' '+include_mode+' "'+'" "'.join(getattr(self,'only_extract_nets',[]))+'"'
	elif hasattr(self,'dont_extract_nets') and len(self.dont_extract_nets) > 0:
		exclude_mode = 'TOPLEVEL'
		if getattr(self,'extract_exclude_recursive',False):
			exclude_mode = 'RECURSIVE'

		selected_nets = 'PEX EXTRACT EXCLUDE '+which_names+' '+exclude_mode+' "'+'" "'.join(getattr(self,'dont_extract_nets',[]))+'"'

	f = open(self.rule_file.abspath(),"w")
	if 1:
	#try:
		f.write("""#!tvf
tvf::VERBATIM {{

LAYOUT PATH "{0}"
LAYOUT PRIMARY "{1}"
LAYOUT SYSTEM GDSII
LAYOUT CASE YES

//LAYOUT RENAME TEXT "/</\\[/g" "/>/\\]/g" """.format(self.layout_gds.abspath(),self.cellname))

		if hasattr(self,'source_netlist'):
			f.write("""

SOURCE PATH "{0}"
SOURCE PRIMARY "{1}"
SOURCE SYSTEM SPICE
SOURCE CASE YES""".format(self.source_netlist.abspath(),self.cellname))


		f.write("""

MASK SVDB DIRECTORY "{1}" QUERY XRC CCI NOPINLOC IXF NXF SLPH

PEX NETLIST "{0}.pex.netlist" HSPICE 1 {2} GROUND "gnd" SEPARATOR "_" LOCATION RCNAMED RLOCATION RWIDTH RLENGTH RLAYER RTHICKNESS
PEX NETLIST SIMPLE "{0}.pex.netlist" HSPICE 1 {2} LOCATION RCNAMED
PEX REPORT "{0}.pex.report" {2}""".format(self.output_file_base.abspath(),self.svdb.abspath(),which_names))

		f.write("""

{0}
PEX REDUCE ANALOG NO
PEX REDUCE MINCAP COMBINE 0.001
PEX REDUCE MINCAP REMOVE 0
PEX REDUCE MINRES COMBINE 0.1
PEX REDUCE MINRES SHORT 0
PEX NETLIST UPPERCASE KEYWORDS NO
PEX NETLIST VIRTUAL CONNECT NO
PEX NETLIST NOXREF NET NAMES NO
PEX NETLIST MUTUAL RESISTANCE YES
//PEX NETLIST ESCAPE CHARACTERS "<>"
PEX NETLIST CHARACTER MAP "<[ >] %_"

//PEX NETLIST GLOBAL NETS pc_pre_buf pc_pst_buf pc_preb_buf sense_pre_buf wen_pst_buf wen_pre_buf enb_int_left writeen_pst_buf


LVS ISOLATE SHORTS YES

LVS POWER NAME
"vdd"
"vdd12a"
"vdd12d"
"vdd25a"
"vdd25d"

LVS GROUND NAME
"gnd"
"gnda"
"gndd"

DRC ICSTATION YES
	""".format(selected_nets))

	#except AttributeError as e:
	#	error_string = str(e)
	#	error_string = error_string.replace('\'task_gen\' object has no','')
	#	Logs.error('Please specify the missing parameter in the task generator call for feature calibre_pex: '+error_string)
	#	return

	for inc in self.includes:
		f.write('\nINCLUDE "'+inc.abspath()+'"')

	for line in getattr(self,'mixins',[]):
		f.write('\n'+line)

	f.write('\n}')
	f.close()

	if len(getattr(self,'xcells',[])) > 0:
		f = open(self.xcells_file.abspath(),"w")
		f.write("\n".join(getattr(self,'xcells',[])))
		f.close()

		f = open(self.hcells_file.abspath(),"w")
		f.write("\n".join(getattr(self,'hcells',[])))
		f.close()


	inputs = [self.layout_gds]
	if hasattr(self,'source_netlist'):
		layout_spice_node = self.svdb.make_node(self.cellname+'.sp')
		#if not os.path.exists(layout_spice_node.abspath()):
		#	from waflib.Errors import WafError
		#	raise WafError('File '+self.cellname+'.sp not found in '+self.svdb.abspath()+' (tool calibre_pex). Probably, you forgot to run LVS first.')

		inputs.append(layout_spice_node)
		inputs.append(self.source_netlist)

	t = self.create_task('calibrePexTask', inputs, self.output_file_base.change_ext(".pex.netlist"))


class calibrePexTask(Task.Task):
	vars = ['CALIBRE_PEX','CALIBRE_PEX_OPT_LVS','CALIBRE_PEX_OPT_PDB','CALIBRE_PEX_OPT_FMT','CALIBRE_PEX_OPT_PHDB']

	def run_phdb(self):
		conditional_options = ""
		#if hasattr(self.generator,'only_extract_nets'): 
		#	conditional_options += ' -select'
		if len(getattr(self.generator,'xcells',[])) > 0:
			conditional_options += ' -hcell '+self.generator.hcells_file.abspath()

		run_str = '%s -xrc -phdb %s %s %s 2>&1' % (self.env.CALIBRE_PEX, conditional_options," ".join(self.env['CALIBRE_PEX_OPT_PHDB']), self.generator.rule_file.abspath())

		out = ""

		try:
			out = self.generator.bld.cmd_and_log(run_str)
		except Exception as e:
			out = e.stdout + e.stderr

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_pex_phdb_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

	def run_pdb(self):
		conditional_options = ""
		if hasattr(self.generator,'only_extract_nets') and len(self.generator.only_extract_nets) > 0:
			conditional_options += ' -select'
		if len(getattr(self.generator,'xcells',[])) > 0:
			conditional_options += ' -full -xcell '+self.generator.xcells_file.abspath()

		run_str = '%s -xrc -pdb %s %s %s 2>&1' % (self.env.CALIBRE_PEX, conditional_options," ".join(self.env['CALIBRE_PEX_OPT_PDB']), self.generator.rule_file.abspath())

		out = ""

		try:
			out = self.generator.bld.cmd_and_log(run_str)
		except Exception as e:
			out = e.stdout + e.stderr

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_pex_pdb_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()


	def run_fmt(self):
		conditional_options = ""
		if len(getattr(self.generator,'xcells',[])) > 0:
			conditional_options = ' -full'
		run_str = '%s -xrc -fmt %s %s %s' % (self.env.CALIBRE_PEX, conditional_options," ".join(self.env['CALIBRE_PEX_OPT_FMT']), self.generator.rule_file.abspath())

		out = ""

		try:
			out = self.generator.bld.cmd_and_log(run_str)
		except Exception as e:
			out = e.stdout + e.stderr

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_pex_fmt_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

	def run_lvs(self):
		conditional_options = ""
		if hasattr(self.generator,'hcells'):
			conditional_options += ' -hcell '+self.generator.hcells_file.abspath()
		run_str = '%s -lvs -hier %s -spice %s %s %s' % (self.env.CALIBRE_PEX, conditional_options ,self.generator.svdb.make_node(self.generator.cellname+'.sp').abspath(), " ".join(self.env['CALIBRE_PEX_OPT_LVS']), self.generator.rule_file.abspath())
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
		if not hasattr(self.generator,'source_netlist'):
			self.run_phdb()
		#self.run_lvs()
		# pdb
		self.run_pdb()
		# fmt
		self.run_fmt()

		return 0


# for convenience
@Configure.conf
def calibre_pex(bld,*k,**kw):
	set_features(kw,'calibre_pex')
	return bld(*k,**kw)


