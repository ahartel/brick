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
        tempdir = tempfile.mkdtemp(dir='rundirs')
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
                # create lib-specific results dir
                CURRENT_RUNDIR.make_node('results/abstract/'+libName).mkdir()
                # create cds.lib in build directory
                bld (
                    rule = "echo 'INCLUDE " + bld.env.ICPRO_DIR + '/' + cdsLibFile + "' > cds.lib",
                )
                # which substeps to perform
                substeps = cell.getElementsByTagName('subStep')
                for substep in substeps:
                    substepName = substep.getAttribute('name').encode('ascii')
                    OUTPUT = CURRENT_RUNDIR.make_node(brick.getTextNodeValue(substep,'outputFile'))
                    #
                    # genLEF
                    #
                    if (substepName == 'genLEF'):
                        skillScript = brick.getTextNodeValue(substep,'skillScript')
                        os.environ['LIB'] = libName
                        os.environ['BLOCK'] = cellName
                        os.environ['ANALIB'] = analib
                        os.environ['TECHLIB'] = techlib
                        os.environ['CELLBASEDIR'] = cellBaseDir

                        bld(
                            name = 'genLEF',
                            rule   = 'abstract -hi -nogui -replay ' + bld.env.ICPRO_DIR + '/' + cellBaseDir + '/' + skillScript + ' -log ' + CURRENT_RUNDIR.make_node('logfiles/').abspath() + '/abstract_' + cellName + '.log',
                            source = [cellBaseDir+'/'+skillScript,cellBaseDir+'/scripts/'+cellName+'.absgen.il'],
                            target = OUTPUT,
                        )
                    #
                    # genLIB
                    #
                    if (substepName == 'genLIB'):
                        TCLscript = brick.getTextNodeValue(substep,'TCLscript')
                        os.environ['LIB'] = libName
                        os.environ['BLOCK'] = cellName
                        os.environ['ANALIB'] = analib
                        os.environ['TECHLIB'] = techlib
                        os.environ['CELLBASEDIR'] = cellBaseDir

                        bld(
                            name = 'genLEF',
                            rule   = 'abstract -hi -nogui -replay ' + bld.env.ICPRO_DIR + '/' + cellBaseDir + '/' + skillScript + ' -log ' + CURRENT_RUNDIR.make_node('logfiles/').abspath() + '/abstract_' + cellName + '.log',
                            source = [cellBaseDir+'/'+skillScript,cellBaseDir+'/scripts/'+cellName+'.absgen.il'],
                            target = OUTPUT,
                        )
                            rule = '../source/perl/verilog2lib.pl ../cdslib/$(LIB)/$(basename $(notdir $*))/functional/verilog.v $@ ./timing/$(basename $(notdir $*))_pincap.txt;',

        #
        # rtl compiler
        #
        if step.getAttribute('class') == 'rc':
            NETLIST = CURRENT_RUNDIR.make_node('results/rtl_compiler/Top_pins.v')
            CURRENT_RUNDIR.make_node('results/rtl_compiler/').mkdir()

            stepBaseDir = brick.getTextNodeValue(step,'stepBaseDir')
            substeps = step.getElementsByTagName('subStep')
            for substep in substeps:
                OUTPUT = CURRENT_RUNDIR.make_node(brick.getTextNodeValue(substep,'outputFile'))
                substepName = substep.getAttribute('name').encode('ascii')
                if (len(substep.getElementsByTagName('after')) > 0):
                    afterName = brick.getTextNodeValue(substep,'after')
                else:
                    afterName = ''
                TCLscript = brick.getTextNodeValue(substep,'TCLscript')

                bld(
                    name = 'compile',
                    rule   = 'rc -64 -f ' + bld.env.ICPRO_DIR + '/units/top/rtl2gds/rtl_compiler/scripts/Top_pins.rtl.tcl -logfile ' + CURRENT_RUNDIR.make_node('logfiles/').abspath() + '/rtl_compiler.log',
                    source = [stepBaseDir+'/'+TCLscript,],
                    target =  OUTPUT,
                )
        #
        # encounter
        #
        if step.getAttribute('class') == 'encounter':
            # TODO: move dir to config
            CURRENT_RUNDIR.make_node('results/encounter/Top_pins_enc').mkdir()
            stepBaseDir = brick.getTextNodeValue(step,'stepBaseDir')
            substeps = step.getElementsByTagName('subStep')
            for substep in substeps:
                OUTPUT = CURRENT_RUNDIR.make_node(brick.getTextNodeValue(substep,'outputFile'))
                substepName = substep.getAttribute('name').encode('ascii')
                if (len(substep.getElementsByTagName('after')) > 0):
                    afterName = brick.getTextNodeValue(substep,'after')
                else:
                    afterName = ''
                TCLscript = brick.getTextNodeValue(substep,'TCLscript')

                bld(
                    name = substepName,
                    after = afterName,
                    rule = 'encounter -init '+ bld.env.ICPRO_DIR + '/units/top/rtl2gds/encounter/' + TCLscript + ' -nowin -log ' + bld.env.CURRENT_RUNDIR + '/logfiles/encounter_'+substepName+'.log',
                    source = [stepBaseDir+'/'+TCLscript,],
                    target = OUTPUT,
                )




