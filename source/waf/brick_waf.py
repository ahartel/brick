import re,os
from xml.dom import minidom

def getLibsFromConfig(xmlconfig,ctx):
    """Gets an xmlconfig object as input and returns
    a dictionary containing the libraries defined in it
    and their according paths"""

    # read libs into dictionary to have access to library paths
    libraries = {}
    libs = xmlconfig.getElementsByTagName('libraries')
    try:
        libs = libs[0].getElementsByTagName('library')
    except IndexError:
        print "No libraries section defined in xmlconfig"

    for lib in libs:
        libName = lib.getAttribute('name').encode('ascii')
        libPath = lib.getAttribute('path').encode('ascii')
        libPath = replace_env_vars(libPath,ctx)
        # check if the path is a folder or a file
        if os.path.isdir(libPath):
            libraries[libName] = libPath
        elif os.path.isfile(libPath):
            parseCdsLib(libPath,libraries,ctx)
        else:
            print "WARNING: path "+libPath+" for library "+libName+" not found"

    return libraries

def parseCdsLib(cdsLib,libraries,ctx):
    f = open(cdsLib, 'r')
    for line in f:
        m = re.search(r"DEFINE\s+([\w]+)\s+(.+)", line)
        if m:
            libName = m.group(1)
            libPath = m.group(2)
            libPath = replace_env_vars(libPath,ctx)
            # find out if this path is relative
            m = re.match(r"\.",libPath)
            if m:
                libPath = os.path.dirname(cdsLib)+'/'+libPath

            if libName in libraries:
                print "WARNING: Library "+libName+" is re-defined in cds.lib file "+cdsLib
            libraries[libName] = libPath
        else:
            m = re.search(r"INCLUDE\s+(.+)", line)
            if m:
                cdsLibPath = m.group(1)
                parseCdsLib(cdsLibPath,libraries)
    f.close()


def getSourceGroups(xmlconfig):
    tests = xmlconfig.getElementsByTagName('tests')
    try:
        sources = tests[0].getElementsByTagName('sources')
        try:
            groups = sources[0].getElementsByTagName('group')
        except IndexError:
            print "No source groups found in xml configuration file"
            return []
    except IndexError:
        print "No sources found in xml configuration file"
        return []
    return groups

def getTestCases(xmlconfig):
    tests = xmlconfig.getElementsByTagName('tests')
    try:
        cases = tests[0].getElementsByTagName('testcases')
        try:
            case = cases[0].getElementsByTagName('testcase')
        except IndexError:
            print "No test case specification found in xml configuration file"
            return []
    except IndexError:
        print "No testcases found in xml configuration file"
        return []
    return case

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
            return ''.join(rc)

def getTextNodeValue(tree,nodeName):
    if tree.getElementsByTagName(nodeName)[0].childNodes:
        return getText(tree.getElementsByTagName(nodeName)[0].childNodes).encode('ascii')
    else:
        return ""

def getTextNodeAsList(context,tree,nodeName):
    textnode = getTextNodeValue(tree,nodeName)
    # remove spaces and line breaks
    textnode = re.sub(r'\s','',textnode)
    textnode = textnode.replace("\n","")
    textnode = replace_env_vars(textnode,context)
    # split the string to make it a list
    list = textnode.split(',')
    # if there was a trailing comma in the string, the last entry will
    # be empty, remove it
    if (len(list[len(list)-1]) == 0):
        list.pop()

    return list

def replace_env_vars(replacestring,context):
    if type(replacestring) == type([]):
        for idx,string in enumerate(replacestring):
            # replace env variables
            m = re.findall('\$(\w+)', string)
            for group in m:
                #for group in m.groups():
                if (context.env[group]):
                    replacestring[idx] = re.sub("\$"+group,context.env[group],string)
                elif (os.environ.has_key(group)):
                    replacestring[idx] = re.sub("\$"+group,os.environ[group],string)

        return replacestring
    else:
        # replace env variables
        m = re.findall('\$(\w+)', replacestring)
        for group in m:
            #for group in m.groups():
            if (context.env[group]):
                replacestring = re.sub("\$"+group,context.env[group],replacestring)
            elif (os.environ.has_key(group)):
                replacestring = re.sub("\$"+group,os.environ[group],replacestring)

        return replacestring

def runStep(subStepName,steps_to_run):
    if steps_to_run[0] == 'all':
        return True
    elif subStepName in steps_to_run:
        return True
    else:
        return False

def checkAlwaysFlag(substepName,steps_to_run):
    if substepName in steps_to_run:
        return True
    else:
        return False

def parseSourceGroups(conf,groups,prefix):
    result = {}
    for group in groups:
        # get group name
        if prefix:
            groupName = prefix+'.'+group.getAttribute('name').encode('ascii')
        else:
            groupName = group.getAttribute('name').encode('ascii')
        result[groupName] = []
        # get filenames, split them, and remove spaces and line breaks
        filenames = getText(group.childNodes).encode('ascii')
        filenames = re.sub(r'\s','',filenames)
        filenames = filenames.replace("\n","")
        # replace env variables
        filenames = replace_env_vars(filenames,conf)
        filenames = filenames.split(",")
        # if this is a relative path and belongs to an included project,
        # give it a prefix
        for name in filenames:
            # if there was a trailing comma in the string, the last entry will
            # be empty, skip it
            if not len(name) == 0:
                if prefix:
                    pattern = re.compile("^\/")
                    if not pattern.match(name):
                        name = 'components/'+prefix+'/'+name
                # append filenames to group's file list
                result[groupName].append(name)

    return result

def parseSearchPaths(xmlconfig,prefix):
    # get string from XML tree
    if xmlconfig.getElementsByTagName('tests')[0].getElementsByTagName('searchpaths')[0].childNodes:
        searchpaths = getTextNodeValue(xmlconfig.getElementsByTagName('tests')[0],'searchpaths')
        # remove spaces and line breaks
        searchpaths = searchpaths.replace(" ","")
        searchpaths = searchpaths.replace("\n","")
        # split the string to make it a list
        splitpaths = searchpaths.split(',')
        searchpaths = []
        for path in splitpaths:
            if prefix:
                pattern = re.compile("^\/")
                if not pattern.match(path):
                    path = 'components/'+prefix+'/'+path
            searchpaths.append(path)
        # if there was a trailing comma in the string, the last entry will
        # be empty, remove it
        if (len(searchpaths[len(searchpaths)-1]) == 0):
            searchpaths.pop()

    return searchpaths

def registerSubProject(conf,projectName):
    if not conf.env.includes:
        conf.env.includes = []
    conf.env.includes.append(projectName) 

def addSearchPaths(conf,searchpaths):
    #
    # process search paths
    #
    # Verilog search paths are basically saved twice.
    # This is because some tools want an '-INCDIR' or '+incdir+' in front
    # of every search path and some tools just want the path itself
    VERILOG_SEARCH_PATHS = {}
    pattern = re.compile("^\/")
    for project,list in searchpaths.iteritems():
        VERILOG_SEARCH_PATHS[project] = []
        for path in list:
            path = replace_env_vars(path,conf)
            # is this path an absolute path?
            if pattern.match(path):
                # add the brick dir-relative path to SEARCH_PATHS
                VERILOG_SEARCH_PATHS[project].append(conf.root.make_node(path).path_from(conf.root.make_node(os.getcwd())))
            # or a BRICK_DIR-relative?
            else:
                VERILOG_SEARCH_PATHS[project].append(path)

    return VERILOG_SEARCH_PATHS

def addIncDirs(conf,searchpaths):
    VERILOG_INC_DIRS = {}
    pattern = re.compile("^\/")
    for project,list in searchpaths.iteritems():
        VERILOG_INC_DIRS[project] = []
        for path in list:
            path = replace_env_vars(path,conf)
            # is this path an absolute path?
            if pattern.match(path):
                # put an '-INCDIR' in front of every entry (cadence syntax)
                if conf.env.simulator == 'cadence':
                    VERILOG_INC_DIRS[project].append('-INCDIR')
                    VERILOG_INC_DIRS[project].append(path)
                elif conf.env.simulator == 'modeltech':
                    VERILOG_INC_DIRS[project].append('+incdir+'+path)
            # or a BRICK_DIR-relative?
            else:
                # the prefix accounts for the tool's being started inside the build folder
                prefix = ''
                if conf.options.out:
                    prefix = conf.path.path_from(conf.path.find_node(conf.options.out))
                else:
                    prefix = conf.path.path_from(conf.path.find_node('rundirs/default'))
                # put an '-INCDIR' in front of every entry (cadence syntax)
                if conf.env.simulator == 'cadence':
                    VERILOG_INC_DIRS[project].append('-INCDIR')
                    VERILOG_INC_DIRS[project].append(prefix+'/'+path)
                elif conf.env.simulator == 'modeltech':
                    VERILOG_INC_DIRS[project].append('+incdir+'+prefix+'/'+path)

    return VERILOG_INC_DIRS

def getSubprojectInfo(conf,path):
    ''' load project_sources from subproject and prepend path'''
    subglobals = {}
    execfile(path+'/wscript',subglobals)

    for name,list in subglobals['project_sources'].iteritems():
        registerSubProject(conf,name)
        new_list = [replace_env_vars(file,conf) if replace_env_vars(file,conf).startswith('/') else replace_env_vars(path+'/'+file,conf) for file in list]
        subglobals['project_sources'][name] = new_list

    for name,list in subglobals['search_paths'].iteritems():
        new_list = [replace_env_vars(file,conf) if replace_env_vars(file,conf).startswith('/') else replace_env_vars(path+'/'+file,conf) for file in list]
        subglobals['search_paths'][name] = new_list


    return subglobals['project_sources'],subglobals['search_paths']

def getProjectSources(conf,source_hash,filter_list):
    new_hash = {}
    for item in filter_list:
        new_hash[item] = replace_env_vars(source_hash[item],conf)
    return new_hash

# -------
# Tasks
# -------

def encounter(task):
    TCLscript = task.inputs[0].abspath()
    logFile = task.outputs[0].abspath()
    cmd = 'encounter -init %s -nowin -overwrite -log %s' % (TCLscript,logFile)
    return task.exec_command(cmd)

def rtl_compiler(task):
    TCLscript = task.inputs[0].abspath()
    logFile = task.outputs[1].abspath()
    cmd = 'rc -64 -f %s -overwrite -logfile %s' % (TCLscript,logFile)
    return task.exec_command(cmd)

def dc_shell(task):
    TCLscript = task.inputs[0].abspath()
    logFile = task.outputs[1].abspath()
    cmd = 'dc_shell -f %s | tee %s 2>&1' % (TCLscript,logFile)
    return task.exec_command(cmd)

def genLEF(task,test):
    mainSkillScript = task.inputs[0].abspath()
    logFile = task.outputs[1].abspath()
    cmd = 'abstract -hi -nogui -replay %s -log %s' % (mainSkillScript,logFile)
    return task.exec_command(cmd)

def genDB(task):
    cmd = 'dc_shell-t -f ../source/tcl/lib2db.tcl'
    return task.exec_command(cmd)

def createCdsLibFile(task):
    src = task.inputs[0].abspath()
    cmd = "echo 'INCLUDE %s' >> cds.lib" % (src)
    return task.exec_command(cmd)

def schematic2verilog(task):
    intermediate = task.outputs[0].abspath()
    tgt = task.outputs[1].abspath()
    log = task.outputs[2].abspath()
    cmd = 'virtuoso -nograph -replay ../source/skill/schem2func.il -log %s && cp %s %s' % (log,intermediate,tgt)
    return task.exec_command(cmd)

def verilog2lib(task):
    verilogFile = task.inputs[0].abspath()
    libFile = task.outputs[0].abspath()
    try:
        pexFile = task.inputs[2].abspath()
        cmd = 'perl ../source/perl/verilog2lib.pl %s %s %s' % (verilogFile,libFile,pexFile)
    except IndexError:
        cmd = 'perl ../source/perl/verilog2lib.pl %s %s' % (verilogFile,libFile)
    return task.exec_command(cmd)

# --------------------------------
# Verilog and VHDL scanner methods
# --------------------------------

def get_sv_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.sv")
    content.extend(dir.ant_glob("*.svh"))
    content.extend(dir.ant_glob("*.v"))
    return content

def get_vhdl_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.vhd")
    return content

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


