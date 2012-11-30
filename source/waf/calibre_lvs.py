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

MASK SVDB DIRECTORY "svdb" QUERY

LVS REPORT "{4}.lvs.report"

LVS REPORT OPTION A AV B BV C CV D E E1 F FX G H I N O P R RA S V W X
LVS REPORT MAXIMUM ALL

LVS RECOGNIZE GATES NONE

DRC ICSTATION YES

LVS POWER  NAME VDD
LVS GROUND NAME GND
	""".format(self.layout_gds.abspath(),self.cellname,self.source_netlist.abspath(),self.cellname,self.cellname))

	for inc in self.includes:
		f.write('\nINCLUDE '+inc.abspath())

	f.close()

	t = self.create_task('calibreLvsTask', [self.layout_gds,self.source_netlist], self.path.make_node(self.cellname+".lvs.report"))



class calibreLvsTask(Task.Task):
	vars = ['CALIBRE_LVS','CALIBRE_LVS_OPTIONS','CALIBRE_LVS_RULES']
	def run(self):
		run_str = '%s -lvs %s %s' % (self.env.CALIBRE_LVS, " ".join(self.env.CALIBRE_LVS_OPTIONS), self.generator.rule_file.abspath())
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


