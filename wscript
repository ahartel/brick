import os,sys,re
import copy
import tempfile
from xml.dom import minidom
sys.path.insert(0, os.path.join('./brick/source/waf'))
import brick_waf

out = 'rundirs/default'

def options(opt):
    # load compiler options for cxx compiler (necessary for systemc testbench)
    opt.load('compiler_c')
    opt.load('compiler_cxx')
    # brICk options
    opt.add_option('--configfile', action='store', default='brick_config.xml', help='XML file containing brICk configuration')
    opt.add_option('--mode', action='store', default='functional', help='switch between \'>build< chip\' or \'>functional< verification\' mode')
    opt.add_option('--rundir', action='store', default='', help='Allows the user to directly name an already existing rundir')
    opt.add_option('--testcase', action='store', default='', help='Choose a testcase as defined in the configfile')
    opt.add_option('--substeps', action='store', default='all', help='which substeps of the build flow should be run?')
    opt.add_option('--simulator', action='store', default='cadence', help='Which simulation software vendor do you want to use? modeltech/[cadence]')

def configure(conf):
    # create the rundir for brick's output and logfiles
    rundir = ''
    if conf.options.out:
        rundir = conf.path.make_node(conf.options.out+'/brick-rundir')
    else:
        rundir = conf.path.make_node(out+'/brick-rundir')
    rundir.mkdir()
    conf.env.CURRENT_RUNDIR = rundir.abspath()

    # create results directory
    conf.root.find_node(conf.env.CURRENT_RUNDIR).make_node('results/').mkdir()
    conf.root.find_node(conf.env.CURRENT_RUNDIR).make_node('logfiles/').mkdir()
    # echo the rundir
    conf.start_msg('Using brICk rundir')
    conf.end_msg(conf.env.CURRENT_RUNDIR)

    # save CWD to env
    conf.env.CWD = os.getcwd()
    # save BRICK_DIR path to config environment
    conf.env.BRICK_DIR = conf.path.find_node('brick').abspath()
    # save SYNOPSYS path to config environment (kind of hacky :)
    conf.env.SYNOPSYS = os.environ['SYNOPSYS']

    # store configuration file
    conf.env.CONFIGFILE = conf.options.configfile

    # load project name from configuration
    xmlconfig = minidom.parse(conf.env.CONFIGFILE) # parse an XML file by name
    conf.env.PROJECTNAME = brick_waf.getTextNodeValue(xmlconfig,'projectShortName')

    # read libs into dictionary to have access to library paths
    conf.env.libraries = brick_waf.getLibsFromConfig(xmlconfig,conf)
    # which mode to run in?
    conf.env.MODE = conf.options.mode
    if (conf.options.mode == 'functional'):
        if not conf.options.simulator:
            conf.env.simulator = 'cadence'
        else:
            conf.env.simulator = conf.options.simulator

        conf.load(conf.env.simulator)
        if conf.env.simulator == 'cadence':
            from cadence import *
            conf.root.find_node(conf.env.CURRENT_RUNDIR).make_node('../worklib/').mkdir()
            # ugly hacking to make cadence C++ compiler visible to waf compiler_c(xx)
            os.environ['CDSROOT'] = '/cad/products/cds/ius82'
            os.environ['PATH'] += ':/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/bin/'
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
        elif conf.env.simulator =='modeltech':
            from modeltech import *
            os.environ['PATH'] += ':/cad/products/modeltech/10.0/modeltech/gcc-4.3.3-linux_x86_64/bin/'
            conf.env.INCLUDES_SYSTEMC = ['/cad/products/modeltech/10.0/modeltech/include/systemc/',
                    ]
        # load compiler options for cxx compiler (necessary for systemc testbench)
        conf.load('compiler_c')
        conf.load('compiler_cxx')

        conf.env['TESTCASE'] = conf.options.testcase

        # declare a list for C/C++ include paths
        conf.env.INCLUDES_SEARCHPATHS = []
        # and add it to the list of used libs
        conf.env.USELIBS = ['SEARCHPATHS']
        # look for components whose source groups should be included 
        conf.env.includes = brick_waf.getTextNodeValue(xmlconfig,'includeComponents')
        conf.env.includes = conf.env.includes.replace("\n","")
        conf.env.includes = conf.env.includes.split(",")

        # iterate through includes and do the following for each include
        # * load source file groups
        # * load searchpaths
        groups = {}
        searchpaths = []
        for include in conf.env.includes:
            includeXmlConfig = minidom.parse('components/'+include+'/brick_config.xml')
            groups.update(brick_waf.parseSourceGroups(conf,brick_waf.getSourceGroups(includeXmlConfig),include))
            searchpaths.extend(brick_waf.parseSearchPaths(includeXmlConfig,include))

        # load search paths of the main project
        searchpaths.extend(brick_waf.parseSearchPaths(xmlconfig,''))

        #
        # Read source file groups
        #
        # The source files that are needed for functional
        # verification tasks are specified in groups in the
        # XML file. These groups are combined to compilation
        # tasks in the next block.
        # This block only collects all the source groups,
        # including those of included brick config files and
        # extends relative paths of included projects by a 
        # prefix 'components/<projectpath>'
        sources = brick_waf.getSourceGroups(xmlconfig)
        testcases = brick_waf.getTestCases(xmlconfig)
        groups.update(brick_waf.parseSourceGroups(conf,sources,''))

        #
        # combine source file groups
        #
        # This block combines the source groups to lists
        # for the different functional verification compilation
        # targets. These are:
        # * RTL sources (called VERILOG_SOURCES here, but containing also VHDL files)
        # * SystemC sources that will be compiled into libncsc_model.so
        # * DPI sources that will be compiled into libdpi.so
        # * Control software sources that will be compiled into ctrlSW executable
        conf.env.VERILOG_SOURCES = []
        conf.env.SYSTEMC_SOURCES = []
        conf.env.DPI_SOURCES = []
        conf.env.SOFTWARE_SOURCES = []
        for testcase in testcases:
            testcaseName = testcase.getAttribute('name').encode('ascii')
            if testcaseName == conf.options.testcase:
                testsources = testcase.getElementsByTagName('sources')
                for source in testsources:
                    sourceName = source.getAttribute('name').encode('ascii')
                    # get group names, split them, and remove spaces and line breaks
                    if source.childNodes:
                        groupnames = brick_waf.getText(source.childNodes).encode('ascii')
                        groupnames = groupnames.replace(" ","")
                        groupnames = groupnames.replace("\n","")
                        groupnames = groupnames.split(",")
                        if (sourceName == 'rtl'):
                            for group in groupnames:
                                conf.env.VERILOG_SOURCES.extend(groups[group])
                        elif (sourceName == 'systemC'):
                            for group in groupnames:
                                conf.env.SYSTEMC_SOURCES.extend(groups[group])
                        elif (sourceName == 'DPI'):
                            for group in groupnames:
                                conf.env.DPI_SOURCES.extend(groups[group])
                        elif (sourceName == 'ctrlSW'):
                            for group in groupnames:
                                conf.env.SOFTWARE_SOURCES.extend(groups[group])
                # assemble simulation tool options and save to waf environment
                testoptions = testcase.getElementsByTagName('option')
                for option in testoptions:
                    optionName = option.getAttribute('tool').encode('ascii')
                    if re.match('USELIB_',optionName):
                        optionName = re.sub(r'USELIB\_','',optionName)
                        optionType = option.getAttribute('type').encode('ascii')
                        optionContent = brick_waf.replace_env_vars(brick_waf.getText(option.childNodes).encode('ascii'),conf)
                        optionContent = optionContent.replace(" ","")
                        optionContent = optionContent.replace("\n","")
                        # write options to env
                        conf.env[optionType+'_'+optionName] = optionContent.split(",")
                        conf.env.USELIBS.append(optionName)
                    else:
                        # get options, split them, and remove spaces and line breaks
                        optionContent = brick_waf.getText(option.childNodes).encode('ascii')
                        optionContent = brick_waf.replace_env_vars(optionContent,conf)
                        optionContent = optionContent.replace(" ","")
                        optionContent = optionContent.replace("\n","")
                        conf.env[optionName+'_OPTIONS'] = optionContent.split(",")


            #
            # process search paths
            #
            conf.env['VERILOG_SEARCH_PATHS'] = []
            conf.env['VERILOG_INC_DIRS'] = []
            pattern = re.compile("^\/")
            for path in searchpaths:
                # is this path an absolute path?
                if pattern.match(path):
                    conf.env.INCLUDES_SEARCHPATHS.append(path)
                    # put an '-INCDIR' in front of every entry (cadence syntax)
                    if conf.env.simulator == 'cadence':
                        conf.env['VERILOG_INC_DIRS'].append('-INCDIR')
                        conf.env['VERILOG_INC_DIRS'].append(path)
                    elif conf.env.simulator == 'modeltech':
                        conf.env['VERILOG_INC_DIRS'].append('+incdir+'+path)
                    # add the brick dir-relative path to SEARCH_PATHS
                    conf.env['VERILOG_SEARCH_PATHS'].append(conf.root.make_node(path).path_from(conf.root.make_node(os.getcwd())))
                # or a BRICK_DIR-relative?
                else:
                    conf.env.INCLUDES_SEARCHPATHS.append(conf.path.abspath()+'/'+path)
                    # the prefix accounts for the tool's being started inside the build folder
                    prefix = ''
                    if conf.options.out:
                        prefix = conf.path.path_from(conf.path.find_node(conf.options.out))
                    else:
                        prefix = conf.path.path_from(conf.path.find_node(out))
                    # put an '-INCDIR' in front of every entry (cadence syntax)
                    if conf.env.simulator == 'cadence':
                        conf.env['VERILOG_INC_DIRS'].append('-INCDIR')
                        conf.env['VERILOG_INC_DIRS'].append(prefix+'/'+path)
                    elif conf.env.simulator == 'modeltech':
                        conf.env['VERILOG_INC_DIRS'].append('+incdir+'+prefix+'/'+path)
                    conf.env['VERILOG_SEARCH_PATHS'].append(path)

    conf.start_msg("Successfully read XML config file for")
    conf.end_msg(conf.env.PROJECTNAME)


def build(bld):
    # translate CURRENT_RUNDIR to path node
    CURRENT_RUNDIR = bld.root.find_node(bld.env.CURRENT_RUNDIR)
    # export results directory
    os.environ['RESULTS_DIR'] = CURRENT_RUNDIR.make_node('results/').abspath()

    # load configuration
    xmlconfig = minidom.parse(bld.env.CONFIGFILE) # parse an XML file by name

    #
    # meta build targets
    #
    # these targets are necessary for the compilers to
    # work properly
    bld.add_group('cdslib')
    bld.set_group('cdslib')
    cdslib_rule = 'echo "" > cds.lib'
    for libName,libPath in bld.env.libraries.iteritems():
        cdslib_rule += ' && echo "DEFINE '+libName+' '+libPath+'" >> cds.lib'
    cdslib_rule += ' && echo "DEFINE worklib '+bld.env.CURRENT_RUNDIR+'/../worklib" >> cds.lib'
    bld (
        rule = cdslib_rule,
        target=CURRENT_RUNDIR.make_node('../cds.lib'),
        source = bld.path.make_node(bld.env.CONFIGFILE)
    )

    bld ( rule = 'echo "DEFINE WORK worklib" > hdl.var' )
    bld ( rule = 'cp ${SRC} ${TGT}', source=bld.root.make_node(bld.env.BRICK_DIR+'/source/cds/si.env'), target=CURRENT_RUNDIR.make_node('../si.env') )

    bld ( rule = 'vlib work', target='./work')

    # start with build jobs or verification jobs
    if (bld.env.MODE == 'build'):
        steps_to_run = []
        try:
            steps_to_run = bld.options.substeps.split(",")
        except AttributeError:
            steps_to_run.append('all')

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
                analib = brick_waf.getTextNodeValue(step,'analib')
                techlib = brick_waf.getTextNodeValue(step,'techlib')
                # get cells to extract
                cells = step.getElementsByTagName('cell')
                for cell in cells:
                    # where ist the current cell and how is it called?
                    cellBaseDir = brick_waf.getTextNodeValue(cell,'cellBaseDir')
                    cellName = cell.getAttribute('name').encode('ascii')
                    libName = cell.getAttribute('lib').encode('ascii')
                    # create lib-specific results dir
                    CURRENT_RUNDIR.make_node('results/abstract/'+libName).mkdir()
                    # which substeps to perform
                    substeps = cell.getElementsByTagName('subStep')
                    for substep in substeps:
                        substepName = substep.getAttribute('name').encode('ascii')
                        #
                        # genGDS
                        #
                        if (substepName == 'genGDS') and brick_waf.runStep(substepName,steps_to_run):
                            bld.add_group('abstract_genGDS_'+cellName)
                            bld.set_group('abstract_genGDS_'+cellName)

                            OUTPUT = [
                                CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.gds'),
                            ]
                            INPUT = [
                                bld.root.make_node(libraries[libName] + '/' + cellName + '/layout/layout.oa'),
                            ]
                            always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                            bld(
                                # export some variables first, before running the abstract generation
                                # since these variables are cell-specific, they have to be export for each task seperately
                                rule = """
                                    export BLOCK=%s && \
                                    strmout -library %s -topCell %s \
                                        -view layout -strmFile %s -logFile %s \
                                        -templateFile %s -userSkillFile %s
                                    """ % (
                                        cellName,
                                        libName,
                                        cellName,
                                        OUTPUT[0].abspath(),
                                        CURRENT_RUNDIR.make_node('logfiles/'+cellName+'_streamout.log').abspath(),
                                        bld.path.make_node('source/skill/streamOut.xstrm').abspath(),
                                        bld.path.make_node('source/skill/set_strmout_cellname.il').abspath()
                                        ),
                                source = INPUT,
                                target = OUTPUT,
                                always = always_flag,
                            )
                        #
                        # genLEF
                        #
                        if (substepName == 'genLEF') and brick_waf.runStep(substepName,steps_to_run):
                            bld.add_group('abstract_genLEF_'+cellName)
                            bld.set_group('abstract_genLEF_'+cellName)

                            skillScript = brick_waf.getTextNodeValue(substep,'skillScript')
                            always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                            OUTPUT = [
                                CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.lef'),
                                CURRENT_RUNDIR.make_node('logfiles/abstract_' + cellName + '.log'),
                            ]
                            INPUT = [
                                bld.path.make_node(cellBaseDir+'/'+skillScript),
                                bld.path.make_node(cellBaseDir+'/scripts/'+cellName+'.absgen.il'),
                                bld.root.make_node(libraries[libName] + '/' + cellName + '/layout/layout.oa'),
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
                                always = always_flag,
                            )
                        #
                        # genDB
                        #
                        if (substepName == 'genDB') and brick_waf.runStep(substepName,steps_to_run):
                            INPUT = CURRENT_RUNDIR.find_node('results/abstract/'+libName+'/'+cellName+'.lib')
                            OUTPUT = CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.db')

                            always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                            bld(
                                rule = """
                                    export LIB=%s && export BLOCK=%s && dc_shell-t -f ../source/tcl/lib2db.tcl""" % (libName,cellName),
                                source = [
                                    CURRENT_RUNDIR.find_node('results/abstract/'+libName+'/'+cellName+'.lib'),
                                    bld.path.find_resource('source/tcl/lib2db.tcl'),
                                ],
                                target = OUTPUT,
                                always = always_flag,
                            )
                        #
                        # genCDL
                        #
                        if (substepName == 'genCDL') and brick_waf.runStep(substepName,steps_to_run):
                            bld.add_group('abstract_genCDL_'+libName+'_'+cellName)
                            INPUT = bld.root.make_node(libraries[libName] + '/' + cellName + '/schematic/sch.oa')
                            OUTPUT = CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.cdl')

                            always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                            bld(
                                rule = """
                                    export LIB=%s && export BLOCK=%s &&
                                    si -batch -command netlist > %s &&
                                    sed "s/\/ //g" %s > %s &&
                                    rm %s
                                """ % (libName,cellName,
                                        CURRENT_RUNDIR.make_node('logfiles/abstract_'+cellName+'.genCDL.log').abspath(),
                                        CURRENT_RUNDIR.make_node('../'+cellName+'.cdl').abspath(),
                                        CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.cdl').abspath(),
                                        CURRENT_RUNDIR.make_node('../'+cellName+'.cdl').abspath()
                                    ),
                                source = INPUT,
                                target = OUTPUT,
                                always = always_flag,
                            )

                        #
                        # genLIB
                        #
                        if (substepName == 'genLIB') and brick_waf.runStep(substepName,steps_to_run):
                            bld.set_group('abstract')
                            always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                            # schematic2verilog
                            INPUT = [
                                bld.root.make_node(libraries[libName] + '/' + cellName + '/schematic/sch.oa'),
                                bld.path.find_resource('source/skill/schem2func.il'),
                            ]
                            OUTPUT = [
                                bld.root.make_node(libraries[libName] + '/' + cellName + '/functional/verilog.v'),
                                CURRENT_RUNDIR.make_node('results/abstract/' + libName + '/' + cellName + '_functional.v'),
                            ]
                            bld(
                                rule = """
                                    export LIB=%s && export BLOCK=%s &&
                                    virtuoso -nograph -replay %s -log %s && cp %s %s""" % (libName,cellName,INPUT[1].abspath(),CURRENT_RUNDIR.make_node("logfiles/abstract_"+cellName+".genfunc.log"),OUTPUT[0].abspath(),OUTPUT[1].abspath()),
                                source = INPUT,
                                target = OUTPUT,
                                always = always_flag,
                            )

                            # verilog2lib
                            INPUT = [
                                CURRENT_RUNDIR.make_node('results/abstract/' + libName + '/' + cellName + '_functional.v'),
                                bld.path.find_resource('source/perl/verilog2lib.pl'),
                            ]
                            try:
                                pincapFile = brick_waf.getTextNodeValue(substep,'pincapFile')
                                INPUT.append(bld.path.make_node(cellBaseDir+'/'+ pincapFile))
                            except (IndexError):
                                pass

                            OUTPUT = CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.lib')
                            bld(
                                rule = brick_waf.verilog2lib,
                                source = INPUT,
                                target = OUTPUT,
                                always = always_flag,
                            )

            #
            # rtl compiler
            #
            if (step.getAttribute('class') == 'rc') and brick_waf.runStep('rc',steps_to_run):
                bld.add_group('rc')
                bld.set_group('rc')
                CURRENT_RUNDIR.make_node('results/rtl_compiler/').mkdir()
                CURRENT_RUNDIR.make_node('results/rtl_compiler/reports').mkdir()
                # get base dir of this step and export it
                stepBaseDir = brick_waf.getTextNodeValue(step,'stepBaseDir')
                os.environ['STEP_BASE_RC'] = bld.path.abspath()+'/'+stepBaseDir
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    TCLscript = brick_waf.getTextNodeValue(substep,'TCLscript')
                    OUTPUT = CURRENT_RUNDIR.make_node('results/rtl_compiler/'+brick_waf.getTextNodeValue(substep,'outputFile'))

                    always_flag = brick_waf.checkAlwaysFlag('rc',steps_to_run)

                    bld(
                        rule   = brick_waf.rtl_compiler,
                        source = [
                            stepBaseDir+'/'+TCLscript,
                        ],
                        target = [
                            OUTPUT,
                            CURRENT_RUNDIR.make_node('logfiles/rtl_compiler.log'),
                        ],
                        always = always_flag,
                    )
            #
            # design compiler
            #
            if (step.getAttribute('class') == 'dc') and brick_waf.runStep('dc',steps_to_run):
                bld.add_group('dc')
                bld.set_group('dc')
                CURRENT_RUNDIR.make_node('results/dc_shell/').mkdir()
                CURRENT_RUNDIR.make_node('results/dc_shell/reports').mkdir()
                # get base dir of this step and export it
                stepBaseDir = brick_waf.getTextNodeValue(step,'stepBaseDir')
                os.environ['STEP_BASE_DC'] = bld.path.abspath()+'/'+stepBaseDir
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    TCLscript = brick_waf.getTextNodeValue(substep,'TCLscript')
                    outputFiles = brick_waf.getTextNodeAsList(bld,substep,'outputFile')
                    OUTPUT = []
                    for path in outputFiles:
                        OUTPUT.append(CURRENT_RUNDIR.make_node('results/dc_shell/'+path))

                    always_flag = brick_waf.checkAlwaysFlag('dc',steps_to_run)

                    bld(
                        rule = 'dc_shell -f %s | tee %s 2>&1' % (bld.path.make_node(stepBaseDir+'/'+TCLscript).abspath(),CURRENT_RUNDIR.make_node('logfiles/dc_shell.log').abspath()),
                        source = [
                            stepBaseDir+'/'+TCLscript,
                        ],
                        target = OUTPUT,
                        always = always_flag,
                        update_outputs=True
                    )

            #
            # encounter
            #
            if step.getAttribute('class') == 'encounter':
                bld.add_group('encounter')
                bld.set_group('encounter')
                # TODO: move dir to config
                CURRENT_RUNDIR.make_node('results/encounter/Top_pins_enc').mkdir()
                CURRENT_RUNDIR.make_node('results/encounter/reports').mkdir()
                stepBaseDir = brick_waf.getTextNodeValue(step,'stepBaseDir')
                # export the stepBaseDir
                os.environ['STEP_BASE_ENC'] = bld.path.abspath()+'/'+stepBaseDir
                # list to hold substep results
                results = {}
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    TCLscript = brick_waf.getTextNodeValue(substep,'TCLscript')
                    # declare list of source files
                    INPUT = []
                    # if this substep has a preceding substep, make this one dependend on its output
                    INPUT.append(bld.path.make_node(stepBaseDir+'/'+TCLscript))
                    if (len(substep.getElementsByTagName('after')) > 0):
                        INPUT.extend(results[brick_waf.getTextNodeValue(substep,'after')])

                    # read output files
                    outputFiles = brick_waf.getTextNodeAsList(bld,substep,'outputFile')
                    OUTPUT = []
                    for path in outputFiles:
                        OUTPUT.append(CURRENT_RUNDIR.make_node(path))

                    results[substepName] = OUTPUT

                    if brick_waf.runStep(substepName,steps_to_run):
                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                        bld(
                            rule = """encounter -init %s -nowin -overwrite -log %s""" % (INPUT[0].abspath(),CURRENT_RUNDIR.make_node('/logfiles/encounter_'+substepName+'.log').abspath()),
                            source = INPUT,
                            target = OUTPUT,
                            always = always_flag,
                        )

            #
            # signoff
            #
            if step.getAttribute('class') == 'signoff':
                bld.add_group('signoff')
                bld.set_group('signoff')
                stepBaseDir = brick_waf.getTextNodeValue(step,'stepBaseDir')
                # export the stepBaseDir
                os.environ['STEP_BASE_SIGNOFF'] = bld.path.abspath()+'/'+stepBaseDir
                # list to hold substep results
                results = {}
                # iterate over substeps
                substeps = step.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    # create a results folder for each substep
                    CURRENT_RUNDIR.make_node('results/signoff/'+substepName).mkdir()
                    #
                    # generate signoff GDS
                    #
                    if (substepName == 'streamin') and brick_waf.runStep(substepName,steps_to_run):
                        inputFile = brick_waf.getTextNodeValue(substep,'inputFile')
                        layermap = brick_waf.getTextNodeValue(substep,'layermap')
                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)
                        libName = substep.getElementsByTagName('streamIn')[0].getAttribute('lib').encode('ascii')
                        cellName = substep.getElementsByTagName('streamIn')[0].getAttribute('cell').encode('ascii')

                        INPUT = [
                            CURRENT_RUNDIR.make_node(inputFile),
                            bld.path.make_node(layermap),
                        ]
                        OUTPUT = bld.root.make_node(libraries[libName] + '/' + cellName + '/layout/layout.oa')

                        bld (
                            rule = """strmin -library %s -topCell %s -view layout -layerMap %s -strmFile %s -logFile %s -snapToGrid
                                """ % (libName,cellName,INPUT[1].abspath(),INPUT[0].abspath(),CURRENT_RUNDIR.make_node('logfiles/streamin_'+libName+'_'+cellName+'.log')),
                            source = INPUT,
                            target = OUTPUT,
                            always = always_flag
                        )
                    elif (substepName == 'streamout') and brick_waf.runStep(substepName,steps_to_run):
                        outputFile = brick_waf.getTextNodeValue(substep,'outputFile')
                        layermap = brick_waf.getTextNodeValue(substep,'layermap')
                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)
                        libName = substep.getElementsByTagName('streamOut')[0].getAttribute('lib').encode('ascii')
                        cellName = substep.getElementsByTagName('streamOut')[0].getAttribute('cell').encode('ascii')

                        INPUT = [
                            bld.root.make_node(libraries[libName] + '/' + cellName + '/layout/layout.oa'),
                            bld.path.make_node(layermap),
                        ]
                        OUTPUT = CURRENT_RUNDIR.make_node(outputFile)

                        bld (
                            rule = """strmout -library %s -topCell %s -view layout -snapToGrid -pathToPolygon -case lower -layerMap %s -strmFile %s -logFile %s""" % (
                                libName,cellName,INPUT[1].abspath(),OUTPUT.abspath(),CURRENT_RUNDIR.make_node('logfiles/streamout_'+libName+'_'+cellName+'.log')),
                            source = INPUT,
                            target = OUTPUT,
                            always = always_flag
                        )
                    #
                    # drc
                    #
                    elif (substepName == 'drc' or substepName == 'antdrc') and brick_waf.runStep(substepName,steps_to_run):
                        ruleFile = brick_waf.getTextNodeValue(substep,'rulefile')
                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                        INPUT = [
                            bld.path.make_node(stepBaseDir+'/'+ruleFile),
                            CURRENT_RUNDIR.make_node('results/encounter/Top_pins.gds')
                                ]
                        # if this substep has a preceding substep, make this one dependend on its output
                        if (len(substep.getElementsByTagName('after')) > 0):
                            INPUT.append(results[brick_waf.getTextNodeValue(substep,'after')])

                        OUTPUT = CURRENT_RUNDIR.make_node('results/signoff/'+brick_waf.getTextNodeValue(substep,'outputFile'))
                        results[substepName] = OUTPUT

                        bld (
                            rule = """calibre -drc -turbo -hyper -64 -hier %s | tee %s""" % (bld.path.make_node(stepBaseDir+'/'+ruleFile).abspath(),CURRENT_RUNDIR.make_node('logfiles/signoff_'+substepName+'.log').abspath()),
                            source = INPUT,
                            target = OUTPUT,
                            always = always_flag,
                        )
                    #
                    # netlist
                    #
                    elif (substepName == 'lvs_netlist') and brick_waf.runStep(substepName,steps_to_run):
                        # sourceNetlist
                        sourceNetlist = brick_waf.getTextNodeValue(substep,'sourceNetlist')
                        # includeVNetlists
                        includeVNetlists = brick_waf.getTextNodeAsList(bld,substep,'includeVNetlists')
                        if len(includeVNetlists) > 0:
                            includeVNetlists = "-v "+(" -v ".join(includeVNetlists))
                        else:
                            includeVNetlists = ""
                        # includeNetlists
                        includeNetlists = brick_waf.getTextNodeAsList(bld,substep,'includeNetlists')
                        if len(includeNetlists) > 0:
                            includeNetlists = "-s "+(" -s ".join(includeNetlists))
                        else:
                            includeNetlists = ""
                        # verilogPrimlib
                        verilogPrimlib = brick_waf.getTextNodeAsList(bld,substep,'verilogPrimlib')
                        if len(verilogPrimlib) > 0:
                            verilogPrimlib = "-l "+(" -l ".join(verilogPrimlib))
                        else:
                            verilogPrimlib = ""

                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                        INPUT = [
                            CURRENT_RUNDIR.make_node(sourceNetlist),
                                ]
                        # if this substep has a preceding substep, make this one dependend on its output
                        if (len(substep.getElementsByTagName('after')) > 0):
                            INPUT.append(results[brick_waf.getTextNodeValue(substep,'after')])

                        OUTPUT = CURRENT_RUNDIR.make_node('results/signoff/'+brick_waf.getTextNodeValue(substep,'outputFile'))
                        results[substepName] = OUTPUT

                        bld (
                            rule = """v2lvs %s -v %s -o %s %s -n -w 3 %s >& %s""" %
                            (
                                # INCLUDE_VNETLISTS
                                includeVNetlists,
                                # source netlist
                                CURRENT_RUNDIR.make_node(sourceNetlist).abspath(),
                                # output netlist
                                CURRENT_RUNDIR.make_node('results/signoff/'+brick_waf.getTextNodeValue(substep,'outputFile')).abspath(),
                                # include netlists
                                includeNetlists,
                                # verilog primlib
                                verilogPrimlib,
                                # logfile
                                CURRENT_RUNDIR.make_node('logfiles/signoff_'+substepName+'.log').abspath()
                            ),
                            source = INPUT,
                            target = OUTPUT,
                            always = always_flag,
                        )

                    #
                    # lvs
                    #
                    elif (substepName == 'lvs') and brick_waf.runStep(substepName,steps_to_run):
                        ruleFile = brick_waf.getTextNodeValue(substep,'rulefile')
                        hcells = brick_waf.getTextNodeValue(substep,'hcellsFile')
                        netlist = brick_waf.getTextNodeValue(substep,'netlist')
                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)

                        INPUT = [
                            bld.path.make_node(stepBaseDir+'/'+ruleFile),
                            CURRENT_RUNDIR.make_node('results/encounter/Top_pins.gds'),
                                ]
                        # if this substep has a preceding substep, make this one dependend on its output
                        if (len(substep.getElementsByTagName('after')) > 0):
                            INPUT.append(results[brick_waf.getTextNodeValue(substep,'after')])

                        OUTPUT = [ CURRENT_RUNDIR.make_node('results/signoff/'+brick_waf.getTextNodeValue(substep,'outputFile')),
                            CURRENT_RUNDIR.make_node('results/signoff/'+netlist),
                        ]
                        results[substepName] = OUTPUT

                        bld (
                            rule = """calibre -lvs -turbo -hyper -64 -hier -hcell %s -spice %s %s | tee %s""" %
                            (
                                bld.path.make_node(stepBaseDir+'/'+hcells).abspath(),
                                CURRENT_RUNDIR.make_node('results/signoff/'+netlist).abspath(),
                                bld.path.make_node(stepBaseDir+'/'+ruleFile).abspath(),
                                CURRENT_RUNDIR.make_node('logfiles/signoff_'+substepName+'.log').abspath()
                            ),
                            source = INPUT,
                            target = OUTPUT,
                            always = always_flag,
                        )
                    #
                    # eps
                    #
                    elif (substepName == 'eps') and brick_waf.runStep(substepName,steps_to_run):
                        substepName = substep.getAttribute('name').encode('ascii')
                        TCLscript = brick_waf.getTextNodeValue(substep,'TCLscript')
                        #outputFiles = brick_waf.getTextNodeAsList(bld,substep,'outputFile')
                        OUTPUT = []
                        #for path in outputFiles:
                        #    OUTPUT.append(CURRENT_RUNDIR.make_node('results/dc_shell/'+path))

                        always_flag = brick_waf.checkAlwaysFlag('eps',steps_to_run)

                        bld(
                            rule = 'eps -init %s -overwrite -log %s' % (bld.path.make_node(stepBaseDir+'/'+TCLscript).abspath(),CURRENT_RUNDIR.make_node('logfiles/eps.log').abspath()),
                            source = [
                                stepBaseDir+'/'+TCLscript,
                            ],
                            target = OUTPUT,
                            always = always_flag,
                            update_outputs=True
                        )
                    #
                    # primetime
                    #
                    elif (substepName == 'primetime') and brick_waf.runStep(substepName,steps_to_run):
                        os.environ['STEP_BASE_PT'] = bld.path.abspath()+'/'+stepBaseDir
                        REPORT_DIR_PT = CURRENT_RUNDIR.make_node('results/signoff/'+substepName+'/reports')
                        REPORT_DIR_PT.mkdir()
                        os.environ['REPORT_DIR_PT'] = REPORT_DIR_PT.abspath()
                        TCLscript = brick_waf.getTextNodeValue(substep,'TCLscript')
                        always_flag = brick_waf.checkAlwaysFlag(substepName,steps_to_run)
                        outputFiles = brick_waf.getTextNodeAsList(bld,substep,'outputFile')
                        corners = brick_waf.getTextNodeAsList(bld,substep,'corners')
                        spefFiles = brick_waf.getTextNodeAsList(bld,substep,'spefFile')

                        INPUT = [
                            bld.path.make_node(stepBaseDir+'/'+TCLscript),
                            CURRENT_RUNDIR.make_node('results/encounter/Top_pins.v'),
                            CURRENT_RUNDIR.make_node('results/encounter/Top_pins.sdc'),
                        ]

                        OUTPUT = []

                        i = 0
                        for corner in corners:
                            INPUT.append(CURRENT_RUNDIR.make_node(spefFiles[i]))
                            OUTPUT.append(CURRENT_RUNDIR.make_node(outputFiles[i]))
                            bld (
                                rule = """
                                    export DESIGN=Top_pins && export NETLIST=%s &&
                                    export SDCFILE=%s && export CORNER=%s &&
                                    export SPEFFILE1=%s && export SPEFFILE2='' && 
                                    pt_shell -file %s 2>&1 > %s"""
                                    % ( INPUT[1].abspath(),
                                    INPUT[2].abspath(),
                                    corner,
                                    INPUT[3].abspath(), 
                                    INPUT[0].abspath(),
                                    CURRENT_RUNDIR.make_node('logfiles/primetime_'+corner+'.log').abspath()
                                ),
                                source = INPUT,
                                target = OUTPUT,
                                always = always_flag,
                            )
                            i=i+1

    # verification tasks are generated from here on
    # if mode was set to 'functional'
    elif bld.env.MODE == 'functional':

        CURRENT_RUNDIR.make_node('rundir').mkdir()

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

        use_libs_systemc = copy.copy(bld.env.USELIBS)
        use_libs_systemc.append('SYSTEMC')

        bld.shlib (
            name = 'libncsc_model.so',
            source = SYSTEMC_SOURCES,
            target = 'ncsc_model',
            use = use_libs_systemc,
        )

        # compilation tasks for DPI
        DPI_SOURCES = []
        for x in bld.env.DPI_SOURCES:
            DPI_SOURCES.append(bld.path.make_node(x))

        bld.shlib (
            name = 'libDPI.so',
            source = DPI_SOURCES,
            target = 'dpi',
            use = bld.env.USELIBS,
        )

        # compilation tasks for independent software
        SOFTWARE_SOURCES = []
        for x in bld.env.SOFTWARE_SOURCES:
            SOFTWARE_SOURCES.append(bld.path.make_node(x))

        bld.program (
            target = 'ctrlSW',
            source = SOFTWARE_SOURCES,
            name = 'ctrlSW',
            use = bld.env.USELIBS,
        )


def run(bld):
    bld.recurse(bld.env.BRICK_DIR+'/source/waf/'+bld.env.simulator)

from waflib.Build import BuildContext
class one(BuildContext):
    cmd = 'run'
    fun = 'run'


def distclean(ctx):
    print(' Not cleaning anything!')


