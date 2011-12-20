import brick_waf

def configure(conf):
    # this is a hack, because, when using ${CURRENT_RUNDIR} directly inside
    # the rule definition of the TaskChains, the concatenation with the
    # logfile name introduces a space between them
    conf.env.VLOG_LOGFILE = conf.env.CURRENT_RUNDIR+'/logfiles/vlog_sv.log'


from waflib import TaskGen
TaskGen.declare_chain(
        name         = 'vlog sv',
        rule         = 'vlog -l ${VLOG_LOGFILE} ${VLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.svh',],
        ext_out      = ['.svh.out',],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner,
)

TaskGen.declare_chain(
        name         = 'vlog sv',
        rule         = 'vlog -l ${VLOG_LOGFILE} ${VLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.sv',],
        ext_out      = ['.sv.out',],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner
)

TaskGen.declare_chain(
        name         = 'vlog verilog2001',
        rule         = 'vlog -l ${VLOG_LOGFILE} ${VLOG_V_OPTIONS} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.v', '.lib.src', '.vp', ],
        reentrant    = False,
        scan         = brick_waf.verilog_scanner
)


