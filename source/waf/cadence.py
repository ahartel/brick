import time
import re
import os
import brick_waf

def configure(conf):
    # this is a hack, because, when using ${CURRENT_RUNDIR} directly inside
    # the rule definition of the TaskChains, the concatenation with the
    # logfile name introduces a space between them
    conf.env.NCVLOG_SV_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncvlog_sv.log'
    conf.env.NCVHDL_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncvhdl.log'
    conf.env.NCVLOG_VAMS_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncvlog_vams.log'
    conf.env.NSDFC_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncsdfc.log'

def load_modules(conf):
    p = subprocess.Popen('module purge && module load umc/u18_13 cds/613 ius/82 mmsim/72 syn/2010.03-SP4 && export -p', shell=True, stdout=subprocess.PIPE)
    time.sleep(1)
    for line in p.stdout:
        m = re.search('(\w+)="(.+)"$', line)
        if (m):
            os.environ[m.group(1)] = m.group(2)

    os.environ['CDSROOT'] = '/cad/products/cds/ius82'
    os.environ['PATH'] += ':/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/bin/'
    return conf

from waflib import TaskGen
TaskGen.declare_chain(
        name         = 'ncvlog sv',
        rule         = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.svh',],
        ext_out      = ['.svh.out',],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner,
)

TaskGen.declare_chain(
        name         = 'ncvlog sv',
        rule         = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.sv',],
        ext_out      = ['.sv.out',],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner
)

TaskGen.declare_chain(
        name         = 'ncvlog verilog2001',
        rule         = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} -work ${WORKLIB} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.v', '.lib.src', '.vp', ],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner
)

TaskGen.declare_chain(
        name         = 'ncvhdl',
        rule         = 'ncvhdl -64bit -logfile ${NCVHDL_LOGFILE} ${NCVHDL_OPTIONS} -work ${WORKLIB} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhd'],
        ext_out      = ['.vhd.out'],
        scan         = brick_waf.vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'ncvhdl',
        rule         = 'ncvhdl -64bit -logfile ${NCVHDL_LOGFILE} ${NCVHDL_OPTIONS} -work ${WORKLIB} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhdl'],
        ext_out      = ['.vhdl.out'],
        scan         = brick_waf.vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'ncvlog vams',
        rule         = 'ncvlog -logfile ${NCVLOG_VAMS_LOGFILE} ${NCVLOG_VAMS_OPTIONS} -work ${WORKLIB} ${VERILOG_SEARCH_PATHS} ${SRC}',
        ext_in       = ['.vams'],
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'ncsdfc',
        rule         = 'ncsdfc -logfile ${NCSDFC_LOGFILE} ${NCSDFC_OPTIONS} ${SRC}',
        ext_in       = ['.sdf','.sdf.gz'],
        reentrant    = False,
)

@TaskGen.feature('*')
def testroot(self):
    self.env.WORKLIB = getattr(self,'worklib','work')
    vsp = getattr(self,'verilog_search_paths',[])
    vid = getattr(self,'verilog_inc_dirs',[])
    self.env.VERILOG_SEARCH_PATHS = vsp
    self.env.VERILOG_INC_DIRS = vid


