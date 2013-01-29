import re,os
from waflib import TaskGen

# --------------------------------
# Verilog and VHDL scanner methods
# --------------------------------

def get_sv_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.sv")
    content.extend(dir.ant_glob("*.svh"))
    content.extend(dir.ant_glob("*.v"))
    return content


def check_files(files,packages,includes_used):
    dependencies = []
    dependency_types = []

    for file in files:
        if len(packages) > 0:
            packages_loadable = set()
            input = open(file.abspath(),'r')
            for line in input:
                m0 = re.search('package\s+(\w+);', line)
                if (m0 is not None):
                    #print "Found package: "+m0.group(1)+" in file "+file.abspath()
                    packages_loadable.add(m0.group(1))
            input.close()
            result = packages & packages_loadable
            if len(result)>0:
                # append the actual source file
                # dependencies.append(file)
                # ... and the generated pseudo-source file
                dependencies.append(file.ctx.bldnode.make_node(file.srcpath()+'.out'))
                dependency_types.append('package')

            packages = packages - packages_loadable
        # add the current file to the depencies if it's an included file
        if os.path.basename(file.abspath()) in includes_used:
            dependencies.append(file)
            dependency_types.append('include')

    #print "Package list after checking files:"+" ".join(packages)
    return packages,dependencies,dependency_types

def verilog_scanner_task(task):
    return task.generator.verilog_scanner(task.inputs[0])

@TaskGen.taskgen_method
def verilog_scanner(self,node):
    debug = False

    input = open(node.abspath(),'r')
    if debug:
        print "Processing file:" + node.abspath()
    # look for used packages and packages that are defined in the input file
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

    if debug:
        print "Packages used:"+" ".join(packages_used)
        print "Packages defined:"+" ".join(packages_defined)
        print "Includes defined:"+" ".join(includes_used)

    input.close()
    # now make use of a very cool python feature: set difference
    packages = packages_used-packages_defined
    # all dependencies will be put into this list
    dependencies = []
    dependency_types = []

    # first look into existing source list
    packages,dependencies,dependency_types = check_files(getattr(self,'source',[]),packages,includes_used)

    if debug:
        print "Package list after checking files:"+" ".join(packages)
        print "Added files after checking source list:"+" ".join([x.abspath() for x in dependencies])

    # then loop through search paths

    # get an instance of the root node
    up = "../"
    for i in range(node.height()-1):
        up += "../"
    rootnode = node.find_dir(up)
    # loop through search paths to find the file that defines the package
    for dir in getattr(self,'verilog_search_paths',[]):
        # get all system verilog files
        files = get_sv_files_from_include_dir(rootnode,dir)
        packages,dir_dependencies,dir_dependency_types = check_files(files,packages,includes_used)
        dependencies.extend(dir_dependencies)
        dependency_types.extend(dir_dependency_types)

    if debug:
        print "Added files after checking include directories:"+" ".join([x.abspath() for x in dependencies])

    return (dependencies,dependency_types)


