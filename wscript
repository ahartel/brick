import os,sys
import tempfile
from xml.dom import minidom
sys.path.insert(0, os.path.join('./source/waf'))
import brick
from cadence import *

def options(opt):
    # load compiler options for cxx compiler (necessary for systemc testbench)
    opt.load('compiler_c')
    opt.load('compiler_cxx')
    # brICk options
    opt.add_option('--configfile', action='store', default='', help='XML file containing brICk configuration')
    opt.add_option('--mode', action='store', default='functional', help='switch between \'>build< chip\' or \'>functional< verification\' mode')
    opt.add_option('--rundir', action='store', default='', help='Allows the user to directly name an already existing rundir')
    opt.add_option('--testcase', action='store', default='', help='Choose a testcase as defined in the configfile')
    opt.add_option('--sim-mixed-signal', action='store_true', default='False', help='Use mixed-signal sources and command options when simulating')

def configure(conf):
    # if the rundir is not set, create a unique rundir
    if (conf.options.rundir):
        conf.env.CURRENT_RUNDIR = conf.path.find_node('build/'+conf.options.rundir).abspath()
    else:
        if (not conf.env.CURRENT_RUNDIR):
            tempdir = tempfile.mkdtemp(dir='build')
            # save tempdir path to config environment
            conf.env.CURRENT_RUNDIR = conf.path.find_node(tempdir).abspath()
            # create results directory
            conf.path.find_node(tempdir).make_node('results/').mkdir()
    conf.start_msg('Using brICk rundir')
    conf.end_msg(conf.env.CURRENT_RUNDIR)

    # save ICPRO_DIR path to config environment
    conf.env.ICPRO_DIR = os.environ['ICPRO_DIR']
    # save SYNOPSYS path to config environment (kind of hacky :)
    conf.env.SYNOPSYS = os.environ['SYNOPSYS']

    # store configuration file
    conf.env.CONFIGFILE = conf.options.configfile

    # load project name from configuration
    xmlconfig = minidom.parse(conf.env.CONFIGFILE) # parse an XML file by name
    conf.env.PROJECTNAME = brick.getTextNodeValue(xmlconfig,'projectShortName')
    conf.start_msg("Successfully read XML config file for")
    conf.end_msg(conf.env.PROJECTNAME)

    # which mode to run in?
    conf.env.MODE = conf.options.mode
    if (conf.options.mode == 'functional'):
        conf.env.MIXED_SIGNAL = conf.options.sim_mixed_signal
        # ugly hacking to make cadence C++ compiler visible to waf compiler_c(xx)
        os.environ['CDSROOT'] = '/cad/products/cds/ius82'
        os.environ['PATH'] += ':/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/bin/'
        # load compiler options for cxx compiler (necessary for systemc testbench)
        conf.load('compiler_c')
        conf.load('compiler_cxx')

        conf.env['TESTCASE'] = conf.options.testcase

        # define systemc-relevant paths
        conf.env.INCLUDES_SYSTEMC = [os.getenv('CDSROOT')+'/tools/systemc/include_pch',
                                    os.getenv('CDSROOT')+'/tools/tbsc/include',
                                    os.getenv('CDSROOT')+'/tools/vic/include',
                                    os.getenv('CDSROOT')+'/tools/ovm/sc/src',
                                    os.getenv('CDSROOT')+'/tools/systemc/include/tlm']
        conf.env.LIBPATH_SYSTEMC = ['/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/install/lib64',
                '/cad/products/cds/ius82/tools/lib',
                '/cad/products/cds/ius82/tools/tbsc/lib/64bit/gnu/4.1',
                '/cad/products/cds/ius82/tools/lib/64bit/SuSE',
                '/cad/products/cds/ius82/tools/systemc/lib/64bit/gnu/4.1']
        conf.env.LIB_SYSTEMC = ['stdc++', 'gcc_s', 'tbsc', 'scv', 'systemc_sh', 'ncscCoSim_sh', 'ncscCoroutines_sh', 'ncsctlm_sh'] # 'ovm', 
        conf.env.RPATH_SYSTEMC = ['/cad/products/cds/ius82/tools/lib/64bit','/cad/products/cds/ius82/tools/tbsc/lib/64bit/gnu/4.1','/cad/products/cds/ius82/tools/systemc/lib/64bit']

        conf.env.USELIBS = ['SYSTEMC']
        #
        # Read source file groups
        #
        sources = xmlconfig.getElementsByTagName('tests')[0].getElementsByTagName('sources')[0].getElementsByTagName('group')
        testcases = xmlconfig.getElementsByTagName('tests')[0].getElementsByTagName('testcases')

        groups = {}
        for group in sources:
            # get group name
            groupName = group.getAttribute('name').encode('ascii')
            groups[groupName] = []
            # get filenames, split them, and remove spaces and line breaks
            filenames = brick.getText(group.childNodes).encode('ascii')
            filenames = filenames.replace(" ","")
            filenames = filenames.replace("\n","")
            # replace env variables
            m = re.search('(?<=\$)(\w+)', filenames)
            if m:
                for group in m.groups():
                    filenames = filenames.replace("$"+group,conf.env[group])
            filenames = filenames.split(",")
            # append filenames to group's file list
            groups[groupName].extend(filenames)
            # if there was a trailing comma in the string, the last entry will
            # be empty, remove it
            if (len(groups[groupName][len(groups[groupName])-1]) == 0):
                groups[groupName].pop()

        #
        # combine source file groups and generate tasks
        #
        conf.env.VERILOG_SOURCES = []
        conf.env.SYSTEMC_SOURCES = []
        for testcase in testcases:
            testsources = testcase.getElementsByTagName('sources')
            for source in testsources:
                sourceName = source.getAttribute('name').encode('ascii')
                # get group names, split them, and remove spaces and line breaks
                groupnames = brick.getText(source.childNodes).encode('ascii')
                groupnames = groupnames.replace(" ","")
                groupnames = groupnames.replace("\n","")
                groupnames = groupnames.split(",")
                if (sourceName == 'rtl'):
                    for group in groupnames:
                        conf.env.VERILOG_SOURCES.extend(groups[group])
                elif (sourceName == 'systemC'):
                    for group in groupnames:
                        conf.env.SYSTEMC_SOURCES.extend(groups[group])
            # assemble simulation tool options and save to waf environment
            testoptions = testcase.getElementsByTagName('option')
            for option in testoptions:
                optionName = option.getAttribute('tool').encode('ascii')
                if re.match('USELIB_',optionName):
                    optionName = re.sub(r'USELIB\_','',optionName)
                    optionType = option.getAttribute('type').encode('ascii')
                    optionContent = brick.getText(option.childNodes).encode('ascii')
                    optionContent = optionContent.replace(" ","")
                    optionContent = optionContent.replace("\n","")
                    # write options to env
                    conf.env[optionType+'_'+optionName] = optionContent.split(",")
                    conf.env.USELIBS.append(optionName)
                else:
                    optionMode = option.getAttribute('mode').encode('ascii')
                    # get options, split them, and remove spaces and line breaks
                    optionContent = brick.getText(option.childNodes).encode('ascii')
                    optionContent = optionContent.replace(" ","")
                    optionContent = optionContent.replace("\n","")
                    if (conf.env.MIXED_SIGNAL == True):
                        if (optionMode == 'mixed-signal'):
                            conf.env[optionName+'_OPTIONS'] = optionContent.split(",")
                    else:
                        if (optionMode == 'rtl'):
                            conf.env[optionName+'_OPTIONS'] = optionContent.split(",")

            # set verilog search paths
            # get string from XML tree
            searchpaths = brick.getTextNodeValue(xmlconfig.getElementsByTagName('tests')[0],'searchpaths')
            # remove spaces and line breaks
            searchpaths = searchpaths.replace(" ","")
            searchpaths = searchpaths.replace("\n","")
            # split the string to make it a list
            searchpaths = searchpaths.split(',')
            # if there was a trailing comma in the string, the last entry will
            # be empty, remove it
            if (len(searchpaths[len(searchpaths)-1]) == 0):
                searchpaths.pop()

            conf.env['VERILOG_SEARCH_PATHS'] = []
            pattern = re.compile("^\/")
            for path in searchpaths:
                # is this path an absolute path?
                if pattern.match(path):
                    conf.env.INCLUDES_SYSTEMC.append(path)
                    # put an '-INCDIR' in front of every entry (cadence syntax)
                    conf.env['VERILOG_SEARCH_PATHS'].append('-INCDIR')
                    conf.env['VERILOG_SEARCH_PATHS'].append(path)
                # or a ICPRO_DIR-relative?
                else:
                    conf.env.INCLUDES_SYSTEMC.append(conf.env.ICPRO_DIR+'/'+path)
                    # put an '-INCDIR' in front of every entry (cadence syntax)
                    conf.env['VERILOG_SEARCH_PATHS'].append('-INCDIR')
                    # the ../ accounts for the tool's being started inside the build folder
                    conf.env['VERILOG_SEARCH_PATHS'].append('../'+path)


    conf.load('cadence')

def build(bld):
    # translate CURRENT_RUNDIR to path node
    CURRENT_RUNDIR = bld.root.find_node(bld.env.CURRENT_RUNDIR)
    # export results directory
    os.environ['RESULTS_DIR'] = CURRENT_RUNDIR.make_node('results/').abspath()
    CURRENT_RUNDIR.make_node('logfiles').mkdir()

    # load configuration
    xmlconfig = minidom.parse(bld.env.CONFIGFILE) # parse an XML file by name
    if (bld.env.MODE == 'build'):
        steps = xmlconfig.getElementsByTagName('tasks')[0].getElementsByTagName('step')
        #
        # step loop
        #
        for step in steps:
            #
            # abstract generation
            #
            if step.getAttribute('class') == 'abstract':
                bld.add_group('abstract')
                bld.set_group('abstract')
                # create results dir for abstracts
                CURRENT_RUNDIR.make_node('results/abstract/').mkdir()
                # get library names for abstract generation
                analib = brick.getTextNodeValue(step,'analib')
                techlib = brick.getTextNodeValue(step,'techlib')
                # get cells to extract
                cells = step.getElementsByTagName('cell')
                for cell in cells:
                    # where ist the current cell and how is it called?
                    cellBaseDir = brick.getTextNodeValue(cell,'cellBaseDir')
                    cellName = cell.getAttribute('name').encode('ascii')
                    libName = cell.getAttribute('lib').encode('ascii')
                    cdsLibFile = brick.getTextNodeValue(cell,'cdsLibFile')
                    cdsLibPath = brick.getTextNodeValue(cell,'cdsLibPath')
                    # create lib-specific results dir
                    CURRENT_RUNDIR.make_node('results/abstract/'+libName).mkdir()
                    # create cds.lib in build directory
                    bld (
                        rule = brick.createCdsLibFile,
                        name = libName+cellName+'createCdsLib',
                        source = bld.path.find_node(cdsLibFile),
                    )
                    # which substeps to perform
                    substeps = cell.getElementsByTagName('subStep')
                    for substep in substeps:
                        substepName = substep.getAttribute('name').encode('ascii')
                        #
                        # genLEF
                        #
                        if (substepName == 'genLEF'):
                            bld.add_group('abstract_genLEF_'+cellName)
                            bld.set_group('abstract_genLEF_'+cellName)

                            skillScript = brick.getTextNodeValue(substep,'skillScript')

                            OUTPUT = [
                                CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.lef'),
                                CURRENT_RUNDIR.make_node('logfiles/abstract_' + cellName + '.log'),
                            ]
                            INPUT = [
                                bld.path.make_node(cellBaseDir+'/'+skillScript),
                                bld.path.make_node(cellBaseDir+'/scripts/'+cellName+'.absgen.il'),
                            ]
                            bld(
                                # export some variables first, before running the abstract generation
                                # since these variables are cell-specific, they have to be export for each task seperately
                                rule = """
                                    export LIB=%s && export BLOCK=%s &&
                                    export ANALIB=%s && export TECHLIB=%s &&
                                    export CELLBASEDIR=%s && abstract -hi -nogui -replay %s -log %s""" % (libName,cellName,analib,techlib,cellBaseDir,INPUT[0].abspath(),OUTPUT[1].abspath()),
                                source = INPUT,
                                target = OUTPUT,
                            )
                        #
                        # genDB
                        #
                        if (substepName == 'genDB'):

                            INPUT = CURRENT_RUNDIR.find_node('results/abstract/'+libName+'/'+cellName+'.lib')
                            OUTPUT = CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.db')
                            bld(
                                rule = """
                                    export LIB=%s && export BLOCK=%s && dc_shell-t -f ../source/tcl/lib2db.tcl""" % (libName,cellName),
                                source = [
                                    CURRENT_RUNDIR.find_node('results/abstract/'+libName+'/'+cellName+'.lib'),
                                    bld.path.find_resource('source/tcl/lib2db.tcl'),
                                ],
                                target = OUTPUT,
                            )

                        #
                        # genLIB
                        #
                        if (substepName == 'genLIB'):
                            bld.set_group('abstract')

                            # schematic2verilog
                            INPUT = [
                                bld.path.make_node(cdsLibPath + '/' + cellName + '/schematic/sch.oa'),
                                bld.path.find_resource('source/skill/schem2func.il'),
                            ]
                            OUTPUT = [
                                bld.path.make_node(cdsLibPath + '/' + cellName + '/functional/verilog.v'),
                                CURRENT_RUNDIR.make_node('results/abstract/' + libName + '/' + cellName + '_functional.v'),
                                CURRENT_RUNDIR.make_node('logfiles' + '/abstract_' + cellName + '.genfunc.log'),
                            ]
                            bld(
                                rule = """
                                    export LIB=%s && export BLOCK=%s &&
                                    virtuoso -nograph -replay %s -log %s && cp %s %s""" % (libName,cellName,INPUT[1].abspath(),OUTPUT[2].abspath(),OUTPUT[0].abspath(),OUTPUT[1].abspath()),
                                source = INPUT,
                                target = OUTPUT,
                            )

                            # verilog2lib
                            INPUT = [
                                CURRENT_RUNDIR.make_node('results/abstract/' + libName + '/' + cellName + '_functional.v'),
                                bld.path.find_resource('source/perl/verilog2lib.pl'),
                            ]
                            OUTPUT = CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.lib')
                            bld(
                                rule = brick.verilog2lib,
                                source = INPUT,
                                target = OUTPUT,
                            )

            #
            # rtl compiler
            #
            if step.getAttribute('class') == 'rc':
                bld.add_group('rc')
                bld.set_group('rc')
                CURRENT_RUNDIR.make_node('results/rtl_compiler/').mkdir()
                CURRENT_RUNDIR.make_node('results/rtl_compiler/reports').mkdir()
                # get base dir of this step and export it
                stepBaseDir = brick.getTextNodeValue(step,'stepBaseDir')
                os.environ['STEP_BASE_RC'] = bld.env.ICPRO_DIR+'/'+stepBaseDir
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    TCLscript = brick.getTextNodeValue(substep,'TCLscript')
                    OUTPUT = CURRENT_RUNDIR.make_node('results/rtl_compiler/'+brick.getTextNodeValue(substep,'outputFile'))
                    bld(
                        rule   = brick.rtl_compiler,
                        source = [
                            stepBaseDir+'/'+TCLscript,
                        ],
                        target = [
                            OUTPUT,
                            CURRENT_RUNDIR.make_node('logfiles/rtl_compiler.log'),
                        ],
    #                    always = True,
                    )
            #
            # design compiler
            #
            if step.getAttribute('class') == 'dc':
                bld.add_group('dc')
                bld.set_group('dc')
                CURRENT_RUNDIR.make_node('results/dc_shell/').mkdir()
                CURRENT_RUNDIR.make_node('results/dc_shell/reports').mkdir()
                # get base dir of this step and export it
                stepBaseDir = brick.getTextNodeValue(step,'stepBaseDir')
                os.environ['STEP_BASE_DC'] = bld.env.ICPRO_DIR+'/'+stepBaseDir
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    TCLscript = brick.getTextNodeValue(substep,'TCLscript')
                    OUTPUT = CURRENT_RUNDIR.make_node('results/dc_shell/'+brick.getTextNodeValue(substep,'outputFile'))
                    bld(
                        rule   = brick.dc_shell,
                        source = [
                            stepBaseDir+'/'+TCLscript,
                        ],
                        target = [
                            OUTPUT,
                            CURRENT_RUNDIR.make_node('logfiles/dc_shell.log'),
                        ],
    #                    always = True,
                    )

            #
            # encounter
            #
            if step.getAttribute('class') == 'encounter':
                bld.add_group('encounter')
                bld.set_group('encounter')
                # TODO: move dir to config
                CURRENT_RUNDIR.make_node('results/encounter/Top_pins_enc').mkdir()
                stepBaseDir = brick.getTextNodeValue(step,'stepBaseDir')
                # export the stepBaseDir
                os.environ['STEP_BASE_ENC'] = bld.env.ICPRO_DIR+'/'+stepBaseDir
                # list to hold substep results
                results = {}
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    TCLscript = brick.getTextNodeValue(substep,'TCLscript')
                    # declare list of source files
                    INPUT = []
                    # if this substep has a preceding substep, make this one dependend on its output
                    INPUT.append(stepBaseDir+'/'+TCLscript)
                    if (len(substep.getElementsByTagName('after')) > 0):
                        INPUT.append(results[brick.getTextNodeValue(substep,'after')])

                    # REMOVE ME!!!
                    if (substepName == "place"):
                        blubb = False
                    else:
                        blubb = True
                    # END REMOVE ME!!!

                    OUTPUT = CURRENT_RUNDIR.make_node(brick.getTextNodeValue(substep,'outputFile'))
                    results[substepName] = OUTPUT
                    bld(
                        rule = brick.encounter,
                        source = INPUT,
                        target = [
                            OUTPUT,
                            CURRENT_RUNDIR.make_node('/logfiles/encounter_'+substepName+'.log')
                        ],
                        always = blubb,
                    )
    # verification tasks are generated from here on
    # if mode was set to 'verify'
    elif bld.env.MODE == 'functional':

        CURRENT_RUNDIR.make_node('worklib').mkdir()
        CURRENT_RUNDIR.make_node('rundir').mkdir()
        bld (
            rule = "echo 'DEFINE worklib "+bld.env.CURRENT_RUNDIR+"/worklib\nINCLUDE ../source/cds/cds.lib\n-- from PDKs tools section: ius\nDEFINE connectLib       $IUS_DIR/tools/affirma_ams/etc/connect_lib/connectLib' > cds.lib",
        )

        bld (
            rule = "echo 'DEFINE WORK worklib' > hdl.var",
        )

        # compilation tasks for verilog/VHDL
        VERILOG_SOURCES = []
        for x in bld.env.VERILOG_SOURCES:
            if (len(x)>0):
                pattern1 = re.compile("^\/")
                pattern2 = re.compile("\*")
                # is this path an absolute path?
                if pattern1.match(x):
                    if pattern2.search(x):
                        VERILOG_SOURCES.extend(bld.root.ant_glob(x))
                    else:
                        VERILOG_SOURCES.append(bld.root.make_node(x))
                else:
                    if pattern2.search(x):
                        VERILOG_SOURCES.extend(bld.path.ant_glob(x))
                    else:
                        VERILOG_SOURCES.append(bld.path.make_node(x))

        bld (
           source = VERILOG_SOURCES,
        )

        # compilation tasks for systemC
        SYSTEMC_SOURCES = []
        for x in bld.env.SYSTEMC_SOURCES:
            SYSTEMC_SOURCES.append(bld.path.make_node(x))

        bld.shlib (
            name = 'libncsc_model.so',
            source = SYSTEMC_SOURCES,
            target = 'ncsc_model',
            use = bld.env.USELIBS,
        )


def run(bld):
    # elaboration
    bld(
        name  = 'elab',
        rule  = 'ncelab ${SIMULATION_TOPLEVEL} -logfile ${CURRENT_RUNDIR}/logfiles/ncelab.log ${NCELAB_OPTIONS} ',
        always = True
    )
    # simulation
    bld(
       rule  = 'ncsim -logfile ${CURRENT_RUNDIR}/logfiles/ncsim.log ${SIMULATION_TOPLEVEL} ${NCSIM_OPTIONS}',
       after = 'elab',
       always = True
    )

from waflib.Build import BuildContext
class one(BuildContext):
    cmd = 'run'
    fun = 'run'



