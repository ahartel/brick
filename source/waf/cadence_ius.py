from verilog_scanner import verilog_scanner_task
from vhdl_scanner import vhdl_scanner
import os

from waflib import Task, TaskGen, Logs

def configure(conf):
	conf.load('brick_general')

	conf.env.NCVLOG_LOGFILE = conf.env.BRICK_LOGFILES+'/ncvlog.log'
	conf.env.NCVLOG_SV_LOGFILE = conf.env.BRICK_LOGFILES+'/ncvlog_sv.log'
	conf.env.NCVHDL_LOGFILE = conf.env.BRICK_LOGFILES+'/ncvhdl.log'
	conf.env.NCVLOG_VAMS_LOGFILE = conf.env.BRICK_LOGFILES+'/ncvlog_vams.log'
	conf.env.NCSDFC_LOGFILE = conf.env.BRICK_LOGFILES+'/ncsdfc.log'
	conf.env.NCELAB_LOGFILE = conf.env.BRICK_LOGFILES+'/ncelab.log'
	conf.env.NCSIM_LOGFILE = conf.env.BRICK_LOGFILES+'/ncsim.log'


TaskGen.declare_chain(
        rule         = 'ncvlog -logfile ${NCVLOG_LOGFILE} ${NCVLOG_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.v', ],
        ext_out      = ['.v.out',],
        reentrant    = False,
        scan         = verilog_scanner_task
)

TaskGen.declare_chain(
        rule         = 'ncvlog -logfile ${NCVLOG_LOGFILE} ${NCVLOG_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = [ '.lib.src',],
        ext_out      = [ '.lib.src.out',],
        reentrant    = False,
        scan         = verilog_scanner_task
)
TaskGen.declare_chain(
        rule         = 'ncvlog -logfile ${NCVLOG_LOGFILE} ${NCVLOG_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = [ '.vp', ],
        ext_out      = [ '.vp.out', ],
        reentrant    = False,
        scan         = verilog_scanner_task
)
TaskGen.declare_chain(
        rule         = 'ncvhdl -64bit -logfile ${NCVHDL_LOGFILE} ${NCVHDL_OPTIONS} -work ${WORKLIB} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhd'],
        ext_out      = ['.vhd.out'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        rule         = 'ncvhdl -64bit -logfile ${NCVHDL_LOGFILE} ${NCVHDL_OPTIONS} -work ${WORKLIB} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhdl'],
        ext_out      = ['.vhdl.out'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        rule         = 'ncvlog -logfile ${NCVLOG_VAMS_LOGFILE} -ams ${NCVLOG_VAMS_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.vams','.va'],
        reentrant    = False,
)

TaskGen.declare_chain(
        rule         = 'ncsdfc -logfile ${NCSDFC_LOGFILE} ${NCSDFC_OPTIONS} ${SRC}',
        ext_in       = ['.sdf','.sdf.gz'],
        reentrant    = False,
)

class CadenceSvlogTask(Task.Task):
	run_str = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} -sv ${NCVLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC[0].abspath()} && echo "${TGT}" > ${TGT}'

@TaskGen.extension(".sv",".svh")
def gen_svlog_task(self,node):
	input = [node]
	output = [node.change_ext(node.suffix()+'.out')]
	sv_task = self.create_task("CadenceSvlogTask",input,output)
	additional_inputs = self.verilog_scanner(input[0])[0]
	sv_task.set_inputs(additional_inputs)


class vlibTask(Task.Task):
	def run(self):
		run_str = 'mkdir -p ${TGT[0].parent.abspath()} && touch ${TGT[0].abspath()}'
		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

@TaskGen.feature('cds_compile_hdl')
def cds_ius_prepare(self):
	# save worklib to env
	self.env.WORKLIB = getattr(self,'worklib','work')
	# create task to generate worklib (if necessary)
	worklib = self.path.make_node(self.env.PROJECT_ROOT+'/'+self.env.WORKLIB+'/.oalib')
	if not getattr(self,'worklib_task',None):
		self.worklib_task = self.create_task('vlibTask',None,worklib.get_bld())
	#
	# transform search paths to the format used for ncvlog
	#
	vsp = getattr(self,'verilog_search_paths',[])
	self.env.VERILOG_SEARCH_PATHS = []
	vid = []
	if len(vsp) > 0:
		for path in vsp:
			self.env.VERILOG_SEARCH_PATHS.append(path.abspath())
			vid.append('-INCDIR')
			vid.append(path.abspath())

	if len(vid) > 0:
		self.env.VERILOG_INC_DIRS = vid

	#
	# scan source files for missing packages or include files
	#
	for node in self.source:
		for input in self.verilog_scanner(node)[0]:
			try:
				self.source.index(input.change_ext(""))
			except ValueError:
				Logs.warn('The included file '+input.change_ext("").abspath()+' is not in your source list for task generator '+self.name+'. Adding it.')
				self.source.append(input.change_ext(""))

@Task.always_run
class ncelabTask(Task.Task):
	def run(self):
		run_str  = 'ncelab '+self.generator.simulation_toplevel+' -logfile ${NCELAB_LOGFILE} ${NCELAB_OPTIONS} '
		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)

@TaskGen.feature('cds_elab')
def cds_ius_elaborate(self):
	try:
		self.simulation_toplevel = self.toplevel
	except AttributeError:
		Logs.error('Please name a toplevel unit for elaboration with feature \'cds_elab\'')
		return -1

	self.create_task("ncelabTask")

@Task.always_run
class ncsimTask(Task.Task):
   run_str = 'ncsim -logfile ${NCSIM_LOGFILE} ${SIMULATION_TOPLEVEL} ${NCSIM_OPTIONS}'

from waflib.TaskGen import feature
@feature('ncsim')
def modelsim_run(self):
	self.env.SIMULATION_TOPLEVEL = self.toplevel
	self.create_task('ncsimTask',None,None)


