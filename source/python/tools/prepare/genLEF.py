from tools.prepare.prepareHook import prepareHook
from prepareError import prepareError
import os

@prepareHook('genLEF')
def prepare_genLEF(brick,sectionName,options):
    "This module needs the option 'input'"

    # this tool needs the cadence module
    if not brick.check_module_loaded('cds'):
        raise prepareError('genLEF failed because module "cds" not loaded.')

    # get input cell view
    try:
        input = brick.get_option(sectionName,'input')
        input_lib,cell_view = input.split('.',2)
        input_cell, input_view = cell_view.split(':',2)
    except ValueError:
        logger.error("Plese give an input of the form lib.cell:view for tool genLEF")
        raise prepareError('genLEF failed')

    # look for library in cds_libs
    lib_path = ''
    for option in brick.config.options('cds_libs'):
        if option == input_lib:
            lib_path = brick.config.get('cds_libs',option,False,{'cwd':os.getcwd()})

    if lib_path == '':
        logger.error("Could not find cds library "+input_lib+" in cds_libs section. Please specify its path.")
        raise prepareError('genLEF failed')

    # generate input file name
    input_filename = brick.get_top_relative_path(os.path.join(lib_path,input_cell,'layout/layout.oa'))

    # generate skill script path
    skill_script = brick.get_top_relative_path(brick.get_option(sectionName,'script'))

    # get analib and techlib
    analib = brick.get_option(sectionName,'analib')
    techlib = brick.get_option(sectionName,'techlib')

    # get logfile
    rundir = brick.get_option(sectionName,'rundir')
    logfile = os.path.join(rundir,'logfiles',sectionName+'.log')
    output_filename = brick.get_top_relative_path(os.path.join(rundir,'results','genLEF',input_lib,input_cell+'.lef'))

    # waf specials
    always = brick.get_option(sectionName,'always',False)
    before = brick.get_option(sectionName,'before','')
    after = brick.get_option(sectionName,'after','')

    # generate wscript code
    wscript_code = """
    OUTPUT_%s = [
        '%s',
    ]
    INPUT_%s = [
        '%s',
        '%s',
    ]
    bld(
        # export some variables first, before running the abstract generation
        # since these variables are cell-specific, they have to be export for each task seperately
        rule = \"""
            export LIB=%s && export BLOCK=%s &&
            export ANALIB=%s && export TECHLIB=%s &&
            abstract -hi -nogui -replay %s -log %s\""",
        source = INPUT_%s,
        target = OUTPUT_%s,
        always = %s,
        before = '%s',
        after = '%s',
    )""" % (sectionName,output_filename,sectionName,input_filename,skill_script,input_lib,input_cell,analib,techlib,skill_script,logfile,sectionName,sectionName,always,before,after)


    return [input_filename,skill_script],[output_filename],wscript_code





