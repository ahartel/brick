from waflib import TaskGen,Task,Logs
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('cadence_base')
	conf.load('cadence_ius')
	conf.load('cadence_netlist')
	conf.load('cadence_config')

        conf.env['CDS_MIXED_SIGNAL'] = True

@TaskGen.feature('cds_mixed_signal')
def gen_cds_mixed_signal_tasks(self):
	(self.libname,self.cellname,self.viewname) = self.get_cadence_lib_cell_view_from_cellview()

	config_node = self.get_cellview_path(self.cellview,True)
	config_node = config_node.make_node('expand.cfg')

	self.netlister_opts = "amsPortConnectionByNameOrOrder=order:useSpectreInfo=spectre veriloga spice symbol"
	self.rundir = "runams_"+self.libname+"_"+self.cellname+"_"+self.viewname
	netlist_node = self.bld.bldnode.make_node(self.rundir+"/netlist/netlist.vams")
	self.source_string_vams = netlist_node.abspath()
	self.env.WORKLIB = getattr(self,'worklib',self.env.CDS_WORKLIB)
	self.logfile = self.get_logdir_node().make_node(self.env.NCVLOG_LOGFILE+'_'+self.rundir).abspath()

	if hasattr(self,'view'):
		self.ncvlog_add_options = ['-VIEW',self.view]
	else:
		self.ncvlog_add_options = []

	if len(self.env.VERILOG_INC_DIRS) > 0:
		self.env.VERILOG_INC_DIRS.extend(['-INCDIR',self.rundir+'/netlist'])
	else:
		self.env.VERILOG_INC_DIRS = ['-INCDIR',self.rundir+'/netlist']

	if not self.netlist == False:
		self.create_task("cdsNetlistTask",config_node,netlist_node)
	if not self.compile == False:
		self.create_task("CadenceVamslogTask",netlist_node)

# vim: noexpandtab:
