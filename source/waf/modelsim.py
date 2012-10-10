from verilog_scanner import verilog_scanner
from vhdl_scanner import vhdl_scanner
import os

def options(opt):
	opt.add_option('--xilinxlib', action='store', help='Define the path to the xilinxlib')

def configure(conf):
	# this is a hack, because, when using ${CURRENT_RUNDIR} directly inside
	# the rule definition of the TaskChains, the concatenation with the
	# logfile name introduces a space between them
	conf.env.VLOG_LOGFILE = conf.env.LOGFILES+'/vlog_sv.log'
	conf.env.VCOM_LOGFILE = conf.env.LOGFILES+'/vcom.log'
	conf.env.VSIM_LOGFILE = conf.env.LOGFILES+'/vsim.log'

	# check xilinxlib
	XILINXLIB = None
	try:
		if conf.options.xilinxlib and os.path.isdir(conf.options.xilinxlib):
			XILINXLIB = conf.convert_string_paths([ conf.options.xilinxlib ])[0]
		else:
			raise AttributeError
	except AttributeError:
		try:
			if os.path.isdir(os.environ['XILINXLIB']):
				XILINXLIB = conf.convert_string_paths([ os.environ['XILINXLIB'] ])[0]
		except KeyError:
			conf.fatal('XILINXLIB not set. Please define a path by setting an environment variable XILINXLIB or by using the option --xilinxlib')

	try:
		conf.env.XILINXLIB = XILINXLIB.abspath()
	except AttributeError:
		conf.fatal('XILINXLIB not set. Please define a path by setting an environment variable XILINXLIB or by using the option --xilinxlib')

	conf.env.INCLUDES_VENDOR = [
		   os.environ['MODEL_SIM_ROOT']+'/include/',
	   ]

from waflib import TaskGen
#TaskGen.declare_chain(
#        rule         = 'vlog -l ${VLOG_LOGFILE} -sv ${VLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
#        ext_in       = ['.svh',],
#        ext_out      = ['.svh.out',],
#        reentrant    = False,
#        scan         = verilog_scanner,
#)
#
#TaskGen.declare_chain(
#        rule         = 'vlog -l ${VLOG_LOGFILE} -sv ${VLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
#        ext_in       = ['.sv',],
#        ext_out      = ['.sv.out',],
#        reentrant    = False,
#        scan         = verilog_scanner
#)

TaskGen.declare_chain(
        rule         = 'vlog -l ${VLOG_LOGFILE} ${VLOG_V_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.v', '.lib.src', '.vp', ],
        reentrant    = False,
        scan         = verilog_scanner
)

TaskGen.declare_chain(
        rule         = 'vcom -l ${VCOM_LOGFILE} ${VCOM_OPTIONS} -work ${WORKLIB} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhd'],
        ext_out      = ['.vhd.out'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

from waflib import Task
class svlogTask(Task.Task):
	run_str = 'vlog -l ${VLOG_LOGFILE} -sv ${VLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC[0].abspath()} && echo "${TGT}" > ${TGT}'

@TaskGen.extension(".sv",".svh")
def gen_svlog_task(self,node):
	input = [node]
	output = [node.change_ext(node.suffix()+'.out')]
	sv_task = self.create_task("svlogTask",input,output)
	additional_inputs = verilog_scanner(sv_task)[0]
	sv_task.set_inputs(additional_inputs)


from waflib import Task
class vlibTask(Task.Task):
	def run(self):
		run_str = 'vlib ${TGT[0].parent.abspath()}'
		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

@TaskGen.feature('modelsim')
def modelsim_prepare(self):
	# save worklib to env
	self.env.WORKLIB = getattr(self,'worklib','work')
	# create task to generate worklib (if necessary)
	worklib = self.path.make_node(self.env.PROJECT_ROOT+'/'+self.env.WORKLIB+'/_info')
	if not getattr(self,'worklib_task',None):
		self.worklib_task = self.create_task('vlibTask',None,worklib.get_bld())

	vsp = getattr(self,'verilog_search_paths',[])
	self.env.VERILOG_SEARCH_PATHS = []
	vid = []
	if len(vsp) > 0:
		for path in vsp:
			self.env.VERILOG_SEARCH_PATHS.append(path.abspath())
			vid.append('+incdir+'+path.abspath())

	if len(vid) > 0:
		self.env.VERILOG_INC_DIRS = vid

@Task.always_run
class vsimTask(Task.Task):
   run_str = 'vsim -l ${VSIM_LOGFILE} ${SIMULATION_TOPLEVEL} ${VSIM_OPTIONS}'

from waflib.TaskGen import feature
@feature('vsim')
def modelsim_run(self):
	self.env.SIMULATION_TOPLEVEL = self.toplevel
	self.create_task('vsimTask',None,None)


