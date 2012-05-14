import os,re,copy,sys
sys.path.insert(0, os.path.join('./source/waf'))
import brick_waf


def options(opt):
    # brICk options
    #opt.add_option('--configfile', action='store', default='brick_config.xml', help='XML file containing brICk configuration')
    opt.add_option('--mode', action='store', default='functional', help='switch between \'>build< chip\' or \'>functional< verification\' mode')
    #opt.add_option('--rundir', action='store', default='', help='Allows the user to directly name an already existing rundir')
    opt.add_option('--testcase', action='store', default='', help='Choose a testcase as defined in the configfile')
    #opt.add_option('--substeps', action='store', default='all', help='which substeps of the build flow should be run?')
    opt.add_option('--simulator', action='store', default='cadence', help='Which simulation software vendor do you want to use? modeltech/[cadence]')


def configure(conf):
    # save CWD to env
    conf.env.CWD = os.getcwd()

    if not conf.env.BRICK_DIR:
        if os.path.isdir(os.getcwd()+'/brick'):
            conf.env.BRICK_DIR = os.getcwd()+'/brick'
        else:
            raise NameError('BRICK_DIR not found')
    else:
        raise NameError('BRICK_DIR not found')

    if not conf.env.BRICK_OPT_RECURSE:
        conf.env.BRICK_OPT_RECURSE = True

        rundir = ''
        if conf.options.out:
            rundir = conf.path.make_node(conf.options.out+'/brick-rundir')
        else:
            rundir = conf.path.make_node('rundirs/default/brick-rundir')
        rundir.mkdir()
        conf.env.CURRENT_RUNDIR = rundir.abspath()

        # create results directory
        conf.root.find_node(conf.env.CURRENT_RUNDIR).make_node('results/').mkdir()
        conf.root.find_node(conf.env.CURRENT_RUNDIR).make_node('logfiles/').mkdir()
        # echo the rundir
        conf.start_msg('Using brICk rundir')
        conf.end_msg(conf.env.CURRENT_RUNDIR)

    # which mode to run in?
    conf.env.MODE = conf.options.mode
    if (conf.options.mode == 'functional'):
        # declare dicts for HDL compile jobs
        if not conf.env.HDL_SOURCES:
            conf.env.HDL_SOURCES = {}
        if not conf.env.HDL_SEARCH_PATHS:
            conf.env.HDL_SEARCH_PATHS = {}
        if not conf.env.HDL_INC_DIRS:
            conf.env.HDL_INC_DIRS = {}

        # load simulator-specific data
        if not conf.options.simulator:
            conf.env.simulator = 'cadence'
        else:
            conf.env.simulator = conf.options.simulator

        conf.load(conf.env.simulator)
        if conf.env.simulator == 'cadence':
            import cadence
            # ugly hacking to make cadence C++ compiler visible to waf compiler_c(xx)
            os.environ['CDSROOT'] = '/cad/products/cds/ius82'
            os.environ['PATH'] += ':/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/bin/'
            # define systemc-relevant paths
            conf.env.INCLUDES_VENDOR = [os.getenv('CDSROOT')+'/tools/systemc/include_pch',
                    os.getenv('CDSROOT')+'/tools/tbsc/include',
                    os.getenv('CDSROOT')+'/tools/vic/include',
                    os.getenv('CDSROOT')+'/tools/ovm/sc/src',
                    os.getenv('CDSROOT')+'/tools/systemc/include/tlm']
            conf.env.LIBPATH_VENDOR = ['/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/install/lib64',
                    '/cad/products/cds/ius82/tools/lib',
                    '/cad/products/cds/ius82/tools/tbsc/lib/64bit/gnu/4.1',
                    '/cad/products/cds/ius82/tools/lib/64bit/SuSE',
                    '/cad/products/cds/ius82/tools/systemc/lib/64bit/gnu/4.1']
            conf.env.LIB_VENDOR = ['stdc++', 'gcc_s', 'tbsc', 'scv', 'systemc_sh', 'ncscCoSim_sh', 'ncscCoroutines_sh', 'ncsctlm_sh'] # 'ovm', 
            conf.env.RPATH_VENDOR = ['/cad/products/cds/ius82/tools/lib/64bit','/cad/products/cds/ius82/tools/tbsc/lib/64bit/gnu/4.1','/cad/products/cds/ius82/tools/systemc/lib/64bit']
        elif conf.env.simulator =='modeltech':
            import modeltech
            # This is the path to the modeltech compiler
            # os.environ['PATH'] += ':/cad/products/modeltech/10.0/modeltech/gcc-4.3.3-linux_x86_64/bin/'
            # however, this compiler is too new! An ABI change has occured
            # so we'll use the cadence compiler
            os.environ['PATH'] += ':/cad/products/cds/ius82/tools/systemc/gcc/4.1-x86_64/bin/'

            conf.env.INCLUDES_VENDOR = [
                os.environ['MODEL_SIM_ROOT']+'/include/',
            ]


def build(bld):
    # translate CURRENT_RUNDIR to path node
    CURRENT_RUNDIR = bld.root.find_node(bld.env.CURRENT_RUNDIR)
    # export results directory
    os.environ['RESULTS_DIR'] = CURRENT_RUNDIR.make_node('results/').abspath()

    #
    # create worklib and component libraries
    #
    # modeltech setup
    if bld.env.simulator == "modeltech":
        bld( rule = 'vlib ./worklib', target = '../worklib/')
        for library in bld.env.includes:
            library = library.replace('-','_')
            bld(rule = 'vlib ./work_'+library, target = '../work_'+library+'/')
    # cadence setup
    elif bld.env.simulator == "cadence":
        cdslib_rule = 'cp '+bld.env.BRICK_DIR+'/source/cds/cds.lib ./'
        for libName,libPath in bld.env.libraries.iteritems():
            cdslib_rule += ' && echo "DEFINE '+libName+' '+libPath+'" >> cds.lib'
        #cdslib_rule += ' && echo "DEFINE worklib ./worklib" >> cds.lib'
        for library in bld.env.includes:
            library = library.replace('-','_')
            cdslib_rule += ' && echo "DEFINE work_'+library+' ./work_'+library+'" >> cds.lib'
            bld (rule = 'mkdir -p ./work_'+library)
        bld (
            rule = cdslib_rule,
            source = bld.root.find_node(bld.env.BRICK_DIR+'/source/cds/cds.lib'),
            #target = 'cds.lib',
        )
        bld ( rule = 'echo "DEFINE WORK worklib" > ./hdl.var', )#target = 'hdl.var' )


    #
    # functional verification
    #
    # verification tasks are generated from here on
    # if mode was set to 'functional'
    if bld.env.MODE == 'functional':

        CURRENT_RUNDIR.make_node('rundir').mkdir()

        # compilation tasks for verilog/VHDL
        for (projectname,project) in bld.env.HDL_SOURCES.iteritems():
            HDL_SOURCES = []
            worklib = 'worklib'
            if not projectname == '__root':
                worklib = 'work_'+projectname.replace('-','_')
            for file in project:
                brick_waf.replace_env_vars(file,bld)
                if (len(file)>0):
                    pattern1 = re.compile("^\/")
                    pattern2 = re.compile("\*")
                    # is this path an absolute path?
                    if pattern1.match(file):
                        if pattern2.search(file):
                            # file[1:] to remove leading slash
                            HDL_SOURCES.extend(bld.root.ant_glob(file[1:]))
                        else:
                            HDL_SOURCES.append(bld.root.make_node(file))
                    else:
                        if pattern2.search(file):
                            HDL_SOURCES.extend(bld.path.ant_glob('../'+file))
                        else:
                            HDL_SOURCES.append(bld.path.make_node('../'+file))

            bld (
               source = HDL_SOURCES,
               worklib = worklib,
               verilog_search_paths = bld.env['HDL_SEARCH_PATHS'][projectname],
               verilog_inc_dirs = bld.env['HDL_INC_DIRS'][projectname],
            )



@TaskGen.feature('static')
@TaskGen.before_method('apply_link')
def make_fully_static(self):
   self.env.SHLIB_MARKER = ''
   self.env.STLIB_MARKER = ''
   self.env.append_unique('LINKFLAGS', '-static')

