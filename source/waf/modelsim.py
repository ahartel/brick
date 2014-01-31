from verilog_scanner import verilog_scanner_task
from vhdl_scanner import vhdl_scanner
import os
import types

def options(opt):
	opt.add_option('--xilinxlib', action='store', help='Define the path to the xilinxlib')

def configure(conf):
	# this is a hack, because, when using ${CURRENT_RUNDIR} directly inside
	# the rule definition of the TaskChains, the concatenation with the
	# logfile name introduces a space between them
	conf.env.VLOG_LOGFILE = conf.env.BRICK_LOGFILES+'/vlog_sv.log'
	conf.env.VCOM_LOGFILE = conf.env.BRICK_LOGFILES+'/vcom.log'
	conf.env.VSIM_LOGFILE = conf.env.BRICK_LOGFILES+'/vsim.log'

	conf.env.INCLUDES_VENDOR = [
		os.environ['MODEL_SIM_ROOT']+'/include/',
	]

from waflib import TaskGen
#TaskGen.declare_chain(
#        rule         = 'vlog -l ${VLOG_LOGFILE} -sv ${VLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
#        ext_in       = ['.svh',],
#        ext_out      = ['.svh.out',],
#        reentrant    = False,
#        scan         = verilog_scanner_task,
#)
#
#TaskGen.declare_chain(
#        rule         = 'vlog -l ${VLOG_LOGFILE} -sv ${VLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
#        ext_in       = ['.sv',],
#        ext_out      = ['.sv.out',],
#        reentrant    = False,
#        scan         = verilog_scanner_task,
#)

TaskGen.declare_chain(
        rule         = 'vlog -l ${VLOG_LOGFILE} ${VLOG_V_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.v', '.lib.src', '.vp', ],
        reentrant    = False,
        scan         = verilog_scanner_task,
)

TaskGen.declare_chain(
        rule         = 'vcom -l ${VCOM_LOGFILE} ${VCOM_OPTIONS} -work ${WORKLIB} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhd'],
        ext_out      = ['.vhd.out'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

from waflib import Task
class ModelsimSvlogTask(Task.Task):
	def run(self):
		files = self.inputs[1:]
		run_str = 'vlog -l ${VLOG_LOGFILE} -sv ${VLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} %s && echo "${TGT}" | tee ${TGT}' % (" ".join([f.abspath() for f in files]),)
		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

@TaskGen.extension(".sv",".svh")
def gen_svlog_task(self,node):
	pass

@TaskGen.feature('modelsim')
@TaskGen.after('process_source')
def bla(self):
	sv_sources = []
	for f in self.source:
		if f.suffix() == '.sv' or f.suffix() == '.svh':
			sv_sources.append(f)

	input = [self.path.get_bld().make_node(getattr(self,'worklib','worklib')+'/_info')] + sv_sources
	output = [node.change_ext(node.suffix()+'.out') for node in sv_sources]
	sv_task = self.create_task("ModelsimSvlogTask",input,output)
	sv_task.scan = types.MethodType(verilog_scanner_task,sv_task)
	# <--- up to here the actual task has been created
	# now we need to make some depencies explicit because
	# the compiler needs those for packages --->
	for f in input[1:]:
		dep_files,dep_types = self.verilog_scanner(f)
		additional_inputs = []
		for dep_file, dep_type in zip(dep_files,dep_types):
			if dep_type == 'package':
				additional_inputs.append(dep_file)
		sv_task.set_inputs(additional_inputs)


from waflib import Task
class vlibTask(Task.Task):
	def run(self):
		run_str = 'vlib -unlocklib ${TGT[0].parent.abspath()}'
		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

@TaskGen.feature('modelsim')
def modelsim_prepare(self):
	# save worklib to env
	wlib = getattr(self,'worklib','worklib')
	# create task to generate worklib (if necessary)
	worklib = self.path.get_bld().make_node(wlib+'/_info')
	if not getattr(self,'worklib_task',None):
		self.worklib_task = self.create_task('vlibTask',None,worklib)

	self.env.WORKLIB = self.path.get_bld().make_node(wlib).abspath()

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
   run_str = 'vsim -l ${VSIM_LOGFILE} -L ${WORKLIB} ${SIMULATION_TOPLEVEL} ${VSIM_OPTIONS}'

from waflib.TaskGen import feature
@feature('vsim')
def modelsim_run(self):
	self.env.SIMULATION_TOPLEVEL = self.toplevel
	worklib = getattr(self,'worklib','worklib')
	# create task to generate worklib (if necessary)
	self.env.WORKLIB = self.path.get_bld().make_node(worklib).abspath()
	self.create_task('vsimTask',None,None)


