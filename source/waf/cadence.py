import subprocess
import time
import re
import os

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

def vhdl_scanner(task):
    # look for used packages and packages that are defined in the input file
    input = open(task.inputs[0].abspath(),'r')
    packages_used = set()
    packages_defined = set()
    includes_used = set()
    for line in input:
        m0 = re.search('package\s+(\w+)\s+is', line)
        m1 = re.search('use\s+work\.(\w+)\.', line)
        if (m0 is not None):
            packages_defined.add(m0.group(1))
        if (m1 is not None):
            packages_used.add(m1.group(1))

    input.close()
    # now make use of a very cool python feature: set difference
    packages = packages_used-packages_defined
    # all dependencies will be put into this list
    dependencies = []
    # get an instance of the root node
    up = "../"
    for i in range(task.inputs[0].height()-1):
        up += "../"
    rootnode = task.inputs[0].find_dir(up)
    # loop through serach paths to find the file that defines the package
    for dir in task.env['VERILOG_SEARCH_PATHS']:
        if (dir == '-INCDIR'):
            continue
        # convert dir to waf node
        dir = rootnode.make_node(os.getcwd()+'/'+dir)
        # get all system verilog files
        files = get_vhdl_files_from_include_dir(rootnode,dir)
        for file in files:
            packages_loadable = set()
            input = open(file.abspath(),'r')
            for line in input:
                m0 = re.search('package\s+(\w+)\s+is', line)
                if (m0 is not None):
                    packages_loadable.add(m0.group(1))
            input.close()
            result = packages & packages_loadable
            if len(result)>0:
                # append the actual source file
                #dependencies.append(file)
                # ... and the generated pseudo-source file
                dependencies.append(file.ctx.bldnode.make_node(file.srcpath()+'.out'))
            # add the current file to the depencies if it's an included file
            if os.path.basename(file.abspath()) in includes_used:
                dependencies.append(file)

    # return dependencies
    return (dependencies,[])

def verilog_scanner(task):
    # look for used packages and packages that are defined in the input file
    input = open(task.inputs[0].abspath(),'r')
    packages_used = set()
    packages_defined = set()
    includes_used = set()
    for line in input:
        m0 = re.search('package\s+(\w+);', line)
        m1 = re.search('import\s+(\w+)[\s:]+', line)
        m2 = re.search('[\s\[](\w+)::', line)
        m3 = re.search('`include\s+"([\w\.]+)"', line)
        if (m0 is not None):
            packages_defined.add(m0.group(1))
        if (m1 is not None):
            packages_used.add(m1.group(1))
        if (m2 is not None):
            packages_used.add(m2.group(1))
        if (m3 is not None):
            includes_used.add(m3.group(1))

    input.close()
    # now make use of a very cool python feature: set difference
    packages = packages_used-packages_defined
    # all dependencies will be put into this list
    dependencies = []
    # get an instance of the root node
    up = "../"
    for i in range(task.inputs[0].height()-1):
        up += "../"
    rootnode = task.inputs[0].find_dir(up)
    # loop through serach paths to find the file that defines the package
    for dir in task.env['VERILOG_SEARCH_PATHS']:
        if (dir == '-INCDIR'):
            continue
        # convert dir to waf node
        dir = rootnode.make_node(os.getcwd()+'/'+dir)
        # get all system verilog files
        files = get_sv_files_from_include_dir(rootnode,dir)
        for file in files:
            packages_loadable = set()
            input = open(file.abspath(),'r')
            for line in input:
                m0 = re.search('package\s+(\w+);', line)
                if (m0 is not None):
                    packages_loadable.add(m0.group(1))
            input.close()
            result = packages & packages_loadable
            if len(result)>0:
                # append the actual source file
                # dependencies.append(file)
                # ... and the generated pseudo-source file
                dependencies.append(file.ctx.bldnode.make_node(file.srcpath()+'.out'))
            # add the current file to the depencies if it's an included file
            if os.path.basename(file.abspath()) in includes_used:
                dependencies.append(file)

    # return dependencies
    return (dependencies,[])

from waflib import TaskGen
TaskGen.declare_chain(
        name         = 'ncvlog sv',
        rule         = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.svh',],
        ext_out      = ['.svh.out',],
        reentrant    = False,
        scan         = verilog_scanner,
)

TaskGen.declare_chain(
        name         = 'ncvlog sv',
        rule         = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.sv',],
        ext_out      = ['.sv.out',],
        reentrant    = False,
        scan         = verilog_scanner
)

TaskGen.declare_chain(
        name         = 'ncvlog verilog2001',
        rule         = 'ncvlog -logfile ${NCVLOG_SV_LOGFILE} ${NCVLOG_SV_OPTIONS} ${VERILOG_INC_DIRS} ${SRC}',
        ext_in       = ['.v', '.lib.src', '.vp', ],
        reentrant    = False,
        scan         = verilog_scanner
)

TaskGen.declare_chain(
        name         = 'ncvhdl',
        rule         = 'ncvhdl -64bit -logfile ${NCVHDL_LOGFILE} ${NCVHDL_OPTIONS} ${SRC} && echo "${TGT}" > ${TGT}',
        ext_in       = ['.vhd'],
        ext_out      = ['.vhd.out'],
        scan         = vhdl_scanner,
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'ncvlog vams',
        rule         = 'ncvlog -logfile ${NCVLOG_VAMS_LOGFILE} ${NCVLOG_VAMS_OPTIONS} ${VERILOG_SEARCH_PATHS} ${SRC}',
        ext_in       = ['.vams'],
        reentrant    = False,
)

TaskGen.declare_chain(
        name         = 'ncsdfc',
        rule         = 'ncsdfc -logfile ${NCSDFC_LOGFILE} ${NCSDFC_OPTIONS} ${SRC}',
        ext_in       = ['.sdf','.sdf.gz'],
        reentrant    = False,
)


def get_sv_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.sv")
    content.extend(dir.ant_glob("*.svh"))
    content.extend(dir.ant_glob("*.v"))
    return content

def get_vhdl_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.vhd")
    return content


