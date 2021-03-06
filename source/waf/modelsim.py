import os
import random
import string
#import types
from verilog_scanner import scan_verilog_task
from vhdl_scanner import vhdl_scanner
from waflib import Task, TaskGen, ConfigSet, Configure, Errors
from brick_general import ChattyBrickTask
from waflib.Utils import to_list

def options(opt):
    opt.add_option('--xilinxlib', action='store',
                   help='Define the path to the xilinxlib')

def configure(conf):
    conf.load('brick_general')
    # this is a hack, because, when using ${CURRENT_RUNDIR} directly inside
    # the rule definition of the TaskChains, the concatenation with the
    # logfile name introduces a space between them
    conf.env.VLOG_LOGFILE = '/vlog_sv.log'
    conf.env.VCOM_LOGFILE = '/vcom.log'
    conf.env.VSIM_LOGFILE = conf.env.BRICK_LOGFILES+'/vsim.log'

    try:
        conf.env.INCLUDES_VENDOR = [
            os.environ['MODEL_SIM_ROOT']+'/include/',
            ]
    except KeyError:
        raise Errors.ConfigurationError('It seems that modelsim hasn\'t been' \
                                        +' installed. Please make sure that' \
                                        +' variable MODEL_SIM_ROOT is defined.')

    conf.env.VSIM_OPTIONS = ['-64']
    conf.env.MODELSIM_WORKLIBS = []

    conf.find_program('vlog',var='MODEL_VLOG')
    conf.find_program('vcom',var='MODEL_VCOM')
    conf.find_program('vsim',var='MODEL_VSIM')
    conf.find_program('vlib',var='MODEL_VLIB')


@TaskGen.taskgen_method
def get_worklib_path_from_string(self,lib):
    worklib = self.bld.bldnode.make_node(lib)
    return worklib

@TaskGen.taskgen_method
def check_create_modelsim_worklib_task(self,lib):
    worklib = self.get_worklib_path_from_string(lib)
    worklib_gen_output = worklib.find_node('_info')
    if worklib_gen_output is None and not getattr(self,'worklib_task',None):
        worklib_gen_output = worklib.make_node('_info')
        worklib_task = self.create_task('vlibTask',None,worklib_gen_output.get_bld())
        return worklib,worklib_gen_output
    else:
        return worklib,None


TaskGen.declare_chain(
        rule         = '${MODEL_VLOG} -l ${VLOG_LOGFILE} ${VLOG_V_OPTIONS} -work ${gen.WORKLIB.abspath()} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.lib.src' ],
        ext_out      = ['.lib.src.out' ],
        reentrant    = False,
        scan         = scan_verilog_task,
        after        = 'vlibTask',
)

TaskGen.declare_chain(
        rule         = '${MODEL_VLOG} -l ${VLOG_LOGFILE} ${VLOG_V_OPTIONS} -work ${gen.WORKLIB.abspath()} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vp', ],
        ext_out      = ['.vp.out', ],
        reentrant    = False,
        scan         = scan_verilog_task,
        after        = 'vlibTask',
)


class ModelsimSvlogTask(Task.Task):
    scan = scan_verilog_task
    run_str = '${MODEL_VLOG} -l ${gen.logfile} -sv ${gen.VLOG_SV_OPTIONS} -work ${gen.WORKLIB.abspath()} ${VERILOG_INC_DIRS} ${gen.source_string_sv}'

class ModelsimVlogTask(Task.Task):
    scan = scan_verilog_task
    run_str = '${MODEL_VLOG} -l ${gen.logfile} ${gen.VLOG_V_OPTIONS} -work ${gen.WORKLIB.abspath()} ${VERILOG_INC_DIRS} ${gen.source_string_v}'

class ModelsimVhdlTask(Task.Task):
    run_str = '${MODEL_VCOM} -l ${gen.logfile} ${gen.VCOM_OPTIONS} -work ' \
              +'${gen.WORKLIB.abspath()} ${gen.source_string_vhdl}'


@TaskGen.before('process_source')
@TaskGen.feature('modelsim')
def modelsim_vlog_prepare(self):
    if hasattr(self,'use'):
        self.VLOG_SV_OPTIONS = []
        self.VLOG_V_OPTIONS = []
        self.VCOM_OPTIONS = []
        uses = to_list(self.use)
        for use in uses:
            if 'VLOG_SV_OPTIONS_'+use in self.env:
                self.VLOG_SV_OPTIONS.extend(self.env['VLOG_SV_OPTIONS_'+use])
            if 'VLOG_V_OPTIONS_'+use in self.env:
                self.VLOG_V_OPTIONS.extend(self.env['VLOG_V_OPTIONS_'+use])
            if 'VCOM_OPTIONS_'+use in self.env:
                self.VCOM_OPTIONS.extend(self.env['VCOM_OPTIONS_'+use])
    else:
        if 'VLOG_SV_OPTIONS' in self.env:
            self.VLOG_SV_OPTIONS = self.env.VLOG_SV_OPTIONS
        else:
            self.VLOG_SV_OPTIONS = []
        if 'VLOG_V_OPTIONS' in self.env:
            self.VLOG_V_OPTIONS = self.env.VLOG_V_OPTIONS
        else:
            self.VLOG_V_OPTIONS = []
        if 'VCOM_OPTIONS' in self.env:
            self.VCOM_OPTIONS = self.env.VCOM_OPTIONS
        else:
            self.VCOM_OPTIONS = []

    # create task to generate worklib (if necessary)
    (self.WORKLIB,worklib_gen_output) = self.check_create_modelsim_worklib_task(getattr(self,'worklib','worklib'))
    #
    # transform search paths to the format used for ncvlog
    #
    vsp = getattr(self,'verilog_search_paths',[])
    self.env.VERILOG_SEARCH_PATHS = []
    vid = []
    if len(vsp) > 0:
        for path in vsp:
            self.env.VERILOG_SEARCH_PATHS.append(path.abspath())
            vid.append('+incdir+'+path.abspath())

    if len(vid) > 0:
        self.env.VERILOG_INC_DIRS = vid

    if not hasattr(self,'name'):
        self.name = Node.split_path(self.source[0])[-1]

    if not hasattr(self,'source'):
        raise Errors.ConfigurationError('Please specify the source attribute for task generator '+getattr(self,'name','?noname? (and give it a name, too!)'))

    # generate the logfile name
    self.logfile = self.get_logdir_node().make_node(self.env.VLOG_LOGFILE+'_'+self.name).abspath()

    # process source here, skip default process_source
    self.source_sv   = []
    self.source_string_sv   = []
    self.source_v    = []
    self.source_string_v    = []
    self.source_vhdl = []
    self.source_string_vhdl = []
    remove_sources = []
    for src in getattr(self,'source',[]):
        if src.suffix() == '.v':
            self.source_string_v.append(src.abspath())
            self.source_v.append(src)
            remove_sources.append(src)
        elif src.suffix() == '.sv' or src.suffix() == '.svh':
            self.source_string_sv.append(src.abspath())
            self.source_sv.append(src)
            remove_sources.append(src)
        elif src.suffix() == '.vhd' or src.suffix() == '.vhdl':
            self.source_string_vhdl.append(src.abspath())
            self.source_vhdl.append(src)
            remove_sources.append(src)

    for src in remove_sources:
        self.source.remove(src)


    if not worklib_gen_output is None:
        self.source_v.append(worklib_gen_output)
        self.source_sv.append(worklib_gen_output)
        self.source_vhdl.append(worklib_gen_output)


    if len(self.source_string_v) > 0:
        task = self.create_task("ModelsimVlogTask", self.source_v,[])
    if len(self.source_string_sv) > 0:
        task = self.create_task("ModelsimSvlogTask", self.source_sv,[])
    if len(self.source_string_vhdl) > 0:
        task = self.create_task("ModelsimVhdlTask", self.source_vhdl,[])


class vlibTask(ChattyBrickTask):
    run_str = '${MODEL_VLIB} ${TGT[0].parent.abspath()}'

    def check_output(self,ret,out):

        return ret

#@TaskGen.feature('modelsim')
#def modelsim_prepare(self):
#   # save worklib to env
#   wlib = getattr(self,'worklib','worklib')
#   # create task to generate worklib (if necessary)
#   worklib = self.path.get_bld()
#   if not os.path.exists(worklib.abspath()):
#       worklib.mkdir()
#   worklib = worklib.make_node(wlib+'/_info')
#
#   if not getattr(self,'worklib_task',None):
#       self.worklib_task = self.create_task('vlibTask',None,worklib)
#
#   self.env.WORKLIB = self.path.get_bld().make_node(wlib).abspath()
#
#   vsp = getattr(self,'verilog_search_paths',[])
#   self.env.VERILOG_SEARCH_PATHS = []
#   vid = []
#   if len(vsp) > 0:
#       for path in vsp:
#           self.env.VERILOG_SEARCH_PATHS.append(path.abspath())
#           vid.append('+incdir+'+path.abspath())
#
#   if len(vid) > 0:
#       self.env.VERILOG_INC_DIRS = vid

@Task.always_run
class vsimTask(Task.Task):
   run_str = '${MODEL_VSIM} -l ${gen.log_file} ${SIMULATION_TOPLEVEL} ${VSIM_OPTIONS} ${gen.vsim_options}'

@TaskGen.feature('vsim')
def modelsim_run(self):
    for lib in self.bld.env.MODELSIM_WORKLIBS:
        self.env.VSIM_OPTIONS.append("-L")
        self.env.VSIM_OPTIONS.append(self.get_worklib_path_from_string(lib).abspath())

    self.vsim_options = getattr(self,'vsim_options',[])
    random_string = ''.join(random.choice(string.lowercase) for i in range(10))
    self.log_file = self.env.VSIM_LOGFILE+'.'+random_string

    self.env.SIMULATION_TOPLEVEL = self.toplevel
    worklib = getattr(self,'worklib','worklib')
    # create task to generate worklib (if necessary)
    self.env.WORKLIB = self.path.get_bld().make_node(worklib).abspath()
    self.create_task('vsimTask',None,None)


# vim: expandtab shiftwidth=4 tabstop=4
