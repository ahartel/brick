import os,sys
import tempfile
from xml.dom import minidom
sys.path.insert(0, os.path.join('./source/waf'))
import brick

def options(opt):
    opt.add_option('--configfile', action='store', default='', help='XML file containing brICk configuration')

def configure(conf):
    # if the rundir is not set, create a unique rundir
    if (not conf.env.CURRENT_RUNDIR):
        tempdir = tempfile.mkdtemp(dir='build')
        # save tempdir path to config environment
        conf.env.CURRENT_RUNDIR = conf.path.find_node(tempdir).abspath()
        # create results directory
        conf.path.find_node(tempdir).make_node('results/').mkdir()

    # save ICPRO_DIR path to config environment
    conf.env.ICPRO_DIR = os.environ['ICPRO_DIR']

    # store configuration file
    conf.env.CONFIGFILE = conf.options.configfile
    # load project name from configuration
    xmlconfig = minidom.parse(conf.env.CONFIGFILE) # parse an XML file by name
    conf.env.PROJECTNAME = brick.getTextNodeValue(xmlconfig,'projectShortName')

def build(bld):
    CURRENT_RUNDIR = bld.root.find_node(bld.env.CURRENT_RUNDIR)
    # export results directory
    os.environ['RESULTS_DIR'] = CURRENT_RUNDIR.make_node('results/').abspath()
    CURRENT_RUNDIR.make_node('logfiles').mkdir()

    # load configuration
    xmlconfig = minidom.parse(bld.env.CONFIGFILE) # parse an XML file by name
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
                        os.environ['LIB'] = libName
                        os.environ['BLOCK'] = cellName

                        INPUT = CURRENT_RUNDIR.find_node('results/abstract/'+libName+'/'+cellName+'.lib')
                        OUTPUT = CURRENT_RUNDIR.make_node('results/abstract/'+libName+'/'+cellName+'.db')
                        bld(
                            rule   = brick.genDB,
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
                        CURRENT_RUNDIR.make_node('logfiles/').abspath() + '/rtl_compiler.log',
                    ]
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

                OUTPUT = CURRENT_RUNDIR.make_node(brick.getTextNodeValue(substep,'outputFile'))
                results[substepName] = OUTPUT
                bld(
                    rule = brick.encounter,
                    source = INPUT,
                    target = [
                        OUTPUT,
                        CURRENT_RUNDIR.make_node('/logfiles/encounter_'+substepName+'.log')
                    ]
                )




