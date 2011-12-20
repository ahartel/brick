import brick_waf

def configure(conf):
    # this is a hack, because, when using ${CURRENT_RUNDIR} directly inside
    # the rule definition of the TaskChains, the concatenation with the
    # logfile name introduces a space between them
    conf.env.NCVLOG_SV_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncvlog_sv.log'
    conf.env.NCVHDL_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncvhdl.log'
    conf.env.NCVLOG_VAMS_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncvlog_vams.log'
    conf.env.NSDFC_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/ncsdfc.log'


from waflib import TaskGen
TaskGen.declare_chain(
        name         = 'vlog sv',
        rule         = 'vlog -l ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.svh',],
        ext_out      = ['.svh.out',],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner,
)

TaskGen.declare_chain(
        name         = 'vlog sv',
        rule         = 'vlog -l ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.sv',],
        ext_out      = ['.sv.out',],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner
)

TaskGen.declare_chain(
        name         = 'vlog verilog2001',
        rule         = 'vlog -l ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.v', '.lib.src', '.vp', ],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner
)

TaskGen.declare_chain(
        name         = 'vhdl',
        rule         = 'vhdl -64bit -l ${NCVHDL_LOGFILE} ${NCVHDL_OPTIONS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhd'],
        ext_out      = ['.vhd.out'],
        scan         = brick_waf.vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'vlog vams',
        rule         = 'vlog -l ${NCVLOG_VAMS_LOGFILE} ${NCVLOG_VAMS_OPTIONS} ${VERILOG_SEARCH_PATHS} ${SRC}',
        ext_in       = ['.vams'],
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'ncsdfc',
        rule         = 'ncsdfc -l ${NCSDFC_LOGFILE} ${NCSDFC_OPTIONS} ${SRC}',
        ext_in       = ['.sdf','.sdf.gz'],
        reentrant    = False,
)
