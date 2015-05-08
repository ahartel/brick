from waflib import TaskGen,Task,Logs
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('cadence_base')
	conf.load('cadence_ius')

@Task.always_run
class runamsTask(ChattyBrickTask):
	shell = True
	run_str = "runams -lib ${gen.lib} -cell ${gen.cell} -view ${gen.view} -netlist all -cdslib ${CDS_LIB_PATH} -hdlvar ${CDS_HDLVAR_PATH} -rundir ${gen.rundir} -netlisteropts \"${gen.netlister_opts}\""

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('ERROR') == 0:
				Logs.error("Error in line %d: %s" % (num,line))
				ret = 1

		return ret


@TaskGen.feature('cds_mixed_signal')
def gen_cds_mixed_signal_tasks(self):
	(self.lib,self.cell,self.view) = self.get_cadence_lib_cell_view_from_cellview()
	#if not self.view == 'config':
	#	Logs.error('Please only use \'config\' cell views with feature \'cds_mixed_signal\'')
	#	return -1
	self.netlister_opts = "amsPortConnectionByNameOrOrder=order:useSpectreInfo=spectre veriloga spice symbol"
	self.rundir = "runams_"+self.lib+"_"+self.cell+"_"+self.view
	netlist_node = self.path.get_bld().make_node(self.rundir+"/netlist/netlist.vams")
	self.source_string_vams = netlist_node.abspath()
	self.env.WORKLIB = getattr(self,'worklib',self.env.CDS_WORKLIB)
	self.logfile_name = self.env.NCVLOG_SV_LOGFILE+'_'+self.rundir
	if len(self.env.VERILOG_INC_DIRS) > 0:
		self.env.VERILOG_INC_DIRS.extend(['-INCDIR',self.rundir+'/netlist'])
	else:
		self.env.VERILOG_INC_DIRS = ['-INCDIR',self.rundir+'/netlist']
	if not self.netlist == False:
		self.create_task("runamsTask",[],netlist_node)
	if not self.compile == False:
		self.create_task("CadenceVamslogTask",netlist_node)

# vim: noexpandtab:
