import re,os,copy
from waflib import TaskGen, Logs

# --------------------------------
# Verilog and VHDL scanner methods
# --------------------------------

def get_sv_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.sv")
    content.extend(dir.ant_glob("*.svh"))
    content.extend(dir.ant_glob("*.v"))
    return content


def check_files(files,packages,includes_used):
    dependencies = set()
    dependency_types = set()
    found_includes = set()

    for file in files:
        if packages and len(packages) > 0:
            packages_loadable = set()
            with open(file.abspath(),'r') as input:
                for line in input:
                    m0 = re.search('package\s+(\w+);', line)
                    if (m0 is not None):
                        #print "Found package: "+m0.group(1)+" in file "+file.abspath()
                        packages_loadable.add(m0.group(1))
            # check if the set of loadable packages and set of packages we are looking
            # for have a non-zero intersection
            result = packages & packages_loadable
            if len(result)>0:
                # append the actual source file
                # dependencies.append(file)
                # ... and the generated pseudo-source file
                dependencies.add(file.ctx.bldnode.make_node(file.srcpath()+'.out'))
                dependency_types.add('package')

            packages = packages - packages_loadable
        # add the current file to the depencies if it's an included file
        if os.path.basename(file.abspath()) in includes_used:
            dependencies.add(file)
            found_includes.add(file)
            dependency_types.add('include')

    #print "Package list after checking files:"+" ".join(packages)
    return packages,dependencies,dependency_types,found_includes

def verilog_scanner_task(task):
    return task.generator.verilog_scanner(task.inputs[0])

@TaskGen.taskgen_method
def verilog_scanner(self,node):

    stack = []
    try:
        return self.scan_verilog_file(node,stack)
    except RuntimeError as e:
        Logs.warn(e)
        return [],[]

@TaskGen.taskgen_method
def scan_verilog_file(self,node,stack):
    debug = False
    if debug:
        print "Processing "+node.abspath()+" with stack "+stack
    if node.abspath() in stack:
        raise RuntimeError("You have an include loop in your files, you should fix that. Package and include order detection? Not gonna happen!\nFile "+node.abspath()+" included by\n\t"+"\n\t".join(stack))
    stack.append(node.abspath())
    with open(node.abspath(),'r') as input:
        if debug:
            print "Processing file:" + node.abspath()
        # look for used packages and packages that are defined in the input file
        packages_used = set()
        packages_defined = set()
        includes_used = set()
        for line in input:
            # Poor man's comment detection
            if line.find('//') == 0:
                continue
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

    # now make use of a very cool python feature: set difference
    packages = packages_used-packages_defined
    # all dependencies will be put into this list
    dependencies = set()
    dependency_types = set()
    found_includes = set()

    # first look into existing source list
    packages,dependencies,dependency_types,found_includes = check_files(getattr(self,'source',[]),packages,includes_used)
    if len(packages) > 0:
		Logs.warn('Package(s) '+' '.join(packages)+' could not be found in any of the given source files. You should fix that!')

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
        # don't look for packages in search paths!
        packages,dir_dependencies,dir_dependency_types,dir_found_includes = check_files(files,None,includes_used)
        dependencies |= dir_dependencies
        dependency_types |= dir_dependency_types
        found_includes |= dir_found_includes

    if debug:
        print "Added files after checking include directories:"+" ".join([x.abspath() for x in dependencies])

    # now recursively scan the include files
    for inc in found_includes:
        if debug:
            print inc
        mystack = copy.copy(stack)
        (add_dependencies, add_dependency_types) = self.scan_verilog_file(inc,mystack)
        dependencies |= set(add_dependencies)
        dependency_types |= set(add_dependency_types)

    return (list(dependencies),list(dependency_types))


