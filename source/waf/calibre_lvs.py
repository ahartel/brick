import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CALIBRE_LVS'] = 'calibre'
	conf.env['CALIBRE_LVS_OPTIONS'] = [
			'-64',
		]


@TaskGen.feature('calibre_lvs')
def create_calibre_lvs_task(self):

	self.rule_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_lvs_rules_'+self.cellname))
	self.hcells_file =  self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_hcells_'+self.cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))

	f = open(self.rule_file.abspath(),"w")
	f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY {1}
LAYOUT SYSTEM GDSII
LAYOUT CASE YES

SOURCE PATH "{2}"
SOURCE PRIMARY "{3}"
SOURCE SYSTEM SPICE
SOURCE CASE YES

MASK SVDB DIRECTORY "{5}" QUERY XRC

LVS REPORT "{4}.lvs.report"

LVS REPORT OPTION A AV B BV C CV D E E1 F FX G H I N O P R RA S V W X
LVS REPORT MAXIMUM ALL

LVS RECOGNIZE GATES NONE

DRC ICSTATION YES

LVS REPORT OPTION NONE
LVS FILTER UNUSED OPTION NONE SOURCE
LVS FILTER UNUSED OPTION NONE LAYOUT

LVS RECOGNIZE GATES ALL
LVS ABORT ON SUPPLY ERROR YES
LVS ISOLATE SHORTS NO
LVS IGNORE PORTS NO
VIRTUAL CONNECT COLON YES
VIRTUAL CONNECT REPORT NO
LVS EXECUTE ERC YES
ERC RESULTS DATABASE "sram_row_pst.erc.results"
ERC SUMMARY REPORT "sram_row_pst.erc.summary" REPLACE HIER
ERC MAXIMUM RESULTS 1000
ERC MAXIMUM VERTEX 4096

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

	""".format(self.layout_gds.abspath(),self.cellname,self.source_netlist.abspath(),self.cellname,self.output_file_base.abspath(),self.svdb.abspath()))

	for inc in self.includes:
		f.write('\nINCLUDE '+inc.abspath())

	f.close()

	if hasattr(self,'hcells'):
		f = open(self.hcells_file.abspath(),"w")
		f.write("\n".join(getattr(self,'hcells',[])))
		f.close()


	t = self.create_task('calibreLvsTask', [self.layout_gds,self.source_netlist], [self.output_file_base.change_ext(".lvs.report"), self.svdb.make_node(self.cellname+'.sp')])



class calibreLvsTask(Task.Task):
	vars = ['CALIBRE_LVS','CALIBRE_LVS_OPTIONS','CALIBRE_LVS_RULES']
	def run(self):
		conditional_options = ""
		if hasattr(self.generator,'hcells'):
			conditional_options += ' -hier -hcell '+self.generator.hcells_file.abspath()
		run_str = '%s -lvs %s -spice %s %s %s' % (self.env.CALIBRE_LVS, conditional_options, self.generator.svdb.make_node(self.generator.cellname+'.sp').abspath()," ".join(self.env.CALIBRE_LVS_OPTIONS), self.generator.rule_file.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_lvs_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

		return 0


# for convenience
@Configure.conf
def calibre_lvs(bld,*k,**kw):
	set_features(kw,'calibre_lvs')
	return bld(*k,**kw)


