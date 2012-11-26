import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './'
	conf.env['CALIBRE_LVS'] = 'calibre'
	conf.env['V2LVS'] = 'v2lvs'
	conf.env['CALIBRE_LVS_OPTIONS'] = [
			'-64',
		]
	conf.env.CALIBRE_LVS_RULES = conf.path.get_bld().make_node(os.path.join(conf.path.bld_dir(),'lvs_rules')).abspath()


@TaskGen.feature('calibre_lvs')
def create_calibre_lvs_task(self):
	# check whether the source_netlist is a lib.cell:view
	# if so, interpose a v2lvs task
	source_netlist = getattr(self,'source_netlist',"")
	if type(source_netlist) == type(""):
		m0 = re.search('(\w+).(\w+):(\w+)', source_netlist)
		if m0:
			source_netlist = self.get_cellview_path(source_netlist).find_node('verilog.vams')

	lvs_netlist = source_netlist.change_ext('.src.net')
	v2lvs_task = self.create_task('v2lvsTask',source_netlist,lvs_netlist)

	f = open(self.env.CALIBRE_LVS_RULES,"w")
	f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY {1}
LAYOUT SYSTEM GDSII
LAYOUT CASE NO

SOURCE PATH "{2}.src.net"
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
	""".format(self.layout_gds.abspath(),self.cellname,lvs_netlist.abspath(),self.cellname,self.cellname))

	for inc in self.includes:
		f.write('\nINCLUDE '+inc.abspath())

	f.close()

	t = self.create_task('calibreLvsTask', [self.layout_gds,lvs_netlist], self.path.make_node(self.cellname+".lvs.report"))

class v2lvsTask(Task.Task):
	run_str = '${V2LVS} -v ${SRC[0].abspath()} -o {TGT[0].abspath()}'
	#v2lvs ${INCLUDE_VNETLISTS} -n -v ${NETLISTSRC} -o ${CELLNAME}.src.net ${INCLUDE_NETLISTS} >& ${LOGFILE2}

@Task.always_run
class calibreLvsTask(Task.Task):
	vars = ['CALIBRE_LVS']
	run_str = '${CALIBRE_LVS} -lvs ${CALIBRE_LVS_OPTIONS} ${CALIBRE_LVS_RULES}'



# for convenience
@Configure.conf
def calibre_lvs(bld,*k,**kw):
	set_features(kw,'calibre_lvs')
	return bld(*k,**kw)


