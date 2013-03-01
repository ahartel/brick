import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs,Context

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

	if not hasattr(self,'cellname'):
		Logs.error('Please name a cell for which to run LVS for feature \'calibre_lvs\'')

	try:
		self.path_cellname = self.cellname[0]
		self.layout_cellname = self.cellname[0]
		self.source_cellname = self.cellname[1]
	except:
		self.path_cellname = self.cellname
		self.layout_cellname = self.cellname
		self.source_cellname = self.cellname

	self.rule_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_lvs_rules_'+self.path_cellname))
	self.hcells_file =  self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_hcells_'+self.path_cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.path_cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))
	if not os.path.exists(self.svdb.abspath()):
		self.svdb.mkdir()

	recognize_gates = getattr(self,'recognize_gates','NONE')
	if recognize_gates == True:
		recognize_gates = 'ALL'

	f = open(self.rule_file.abspath(),"w")
	f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY "{1}"
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
LVS ISOLATE SHORTS NO
LVS IGNORE PORTS NO
LVS GLOBALS ARE PORTS NO
VIRTUAL CONNECT COLON YES
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

	if len(getattr(self,'hcells',[])) > 0:
		f = open(self.hcells_file.abspath(),"w")
		f.write("\n".join(getattr(self,'hcells',[])))
		f.close()

	output = self.svdb.make_node(self.layout_cellname+'.sp')
	open(output.abspath(),'w').close() 

	t = self.create_task('calibreLvsTask', [self.layout_gds,self.source_netlist], [self.output_file_base.change_ext(".lvs.report"), output])

class calibreLvsTask(Task.Task):
	vars = ['CALIBRE_LVS','CALIBRE_LVS_OPTIONS','CALIBRE_LVS_RULES']
	def run(self):
		conditional_options = ""
		if len(getattr(self,'hcells',[])) > 0:
			conditional_options += ' -hcell '+self.generator.hcells_file.abspath()

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_lvs_'+self.generator.path_cellname+'.log'))

		run_str = '%s -lvs %s -spice %s %s %s > %s 2>&1' % (self.env.CALIBRE_LVS, conditional_options, self.generator.svdb.make_node(self.generator.layout_cellname+'.sp').abspath()," ".join(self.env.CALIBRE_LVS_OPTIONS), self.generator.rule_file.abspath(),logfile.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stderr

		found_error = 0
		with open(logfile.abspath(),'r') as lgf:
			for line in lgf:
				if re.match('LVS completed. INCORRECT',line):
					print line
					found_error = 1
				elif re.match('ERROR:',line):
					print line
					found_error = 1
				#elif re.match('@W: CL218',line):
				#	print line
				#	found_error = 1

		return found_error

		return 0

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
