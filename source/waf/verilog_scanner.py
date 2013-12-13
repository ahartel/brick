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

@TaskGen.taskgen_method
def check_files(self,files,packages,includes_used,debug=False):
    dependencies = []
    dependency_types = []
    found_includes = []

    for file in files:
        if packages and len(packages) > 0:
            packages_loadable = set()
            with open(file.abspath(),'r') as input:
                for line in input:
                    m0 = re.search('package\s+(\w+);', line)
                    if (m0 is not None):
                        package_name = m0.group(1)
                        if debug: print "Found package: "+package_name+" in file "+file.abspath()
                        packages_loadable.add(package_name)
                        if not self.package_cache.has_key(package_name):
                            self.package_cache[package_name] = file.change_ext('.sv.out')
                        else:
                            if self.package_cache[package_name].abspath() != file.change_ext('.sv.out').abspath():
                                raise RuntimeError("Package "+package_name+" defined in "+file.abspath()+" but has already been found in "+self.package_cache[package_name].abspath()+".")

            # check if the set of loadable packages and set of packages we are looking
            # for have a non-zero intersection
            result = packages & packages_loadable
            if len(result)>0:
                # append the actual source file
                # dependencies.append(file)
                # ... and the generated pseudo-source file
                if debug: print "Adding file "+file.abspath()+" to dependency list as package."
                dependencies.append(file.ctx.bldnode.make_node(file.srcpath()+'.out'))
                dependency_types.append('package')

            packages = packages - packages_loadable
        # add the current file to the depencies if it's an included file
        if os.path.basename(file.abspath()) in includes_used:
            dependencies.append(file)
            found_includes.append(file)
            dependency_types.append('include')

    return packages,dependencies,dependency_types,found_includes

def verilog_scanner_task(task):
    return task.generator.verilog_scanner(task.inputs[0])

@TaskGen.taskgen_method
def verilog_scanner(self,node,debug=False):

    stack = []
    try:
        return self.scan_verilog_file(node,stack,debug)
    except RuntimeError as e:
        Logs.warn(e)
        return [],[]

@TaskGen.taskgen_method
def scan_verilog_file(self,node,stack,debug=False):

    if node.abspath() in stack:
        raise RuntimeError("You have an include loop in your files, you should fix that. Package and include order detection? Not gonna happen!\nFile "+node.abspath()+" included by\n\t"+"\n\t".join(stack))
    stack.append(node.abspath())

    # This is the basic check, that looks in the current file for:
    #  - packages defined
    #  - packages used/imported
    #  - files included
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
            m2 = re.search('[\s\[\-+*\/](\w+)::', line)
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
    missing_packages = packages_used-packages_defined
    # cache package origins
    for package in packages_defined:
        self.package_cache[package] = node.change_ext('.sv.out')

    # all dependencies will be put into this list
    dependencies = []
    dependency_types = []
    found_includes = []

    # look if missing packages are alread in the cache dict
    packages_known = set()
    for package in missing_packages:
        if self.package_cache.has_key(package):
            dependencies.append(self.package_cache[package])
            dependency_types.append('package')
            packages_known.add(package)

    missing_packages -= packages_known

    if debug: print "Missing packages after checking package cache:"+" ".join(missing_packages)
    if debug: print "Added dependencies after checking cache:"+" ".join([x.abspath() for x in dependencies])

    # first look into existing source list
    # check the source list of the current taskgen for the
    # existance of the necessary packages
    if len(missing_packages) > 0:
        missing_packages,check_deps,check_dep_types,check_found_incs = self.check_files(getattr(self,'source',[]),missing_packages,includes_used,debug)
        if debug: print "Missing packages after checking files in self.source:"+" ".join(missing_packages)
    #if len(packages) > 0:
	#	Logs.warn('Package(s) '+' '.join(packages)+' could not be found in any of the given source files. You should fix that!')

        dependencies.extend(check_deps)
        dependency_types.extend(check_dep_types)
        found_includes.extend(check_found_incs)

        if debug:
            print "Added files after checking source list:"+"\n ".join([x.abspath() for x in check_deps])
            print "Dependencies after checking source list:"+" ".join([x.abspath() for x in dependencies])

    # if the used packages could not be found in the source list of the current taskgen
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
        # don't look for packages in search paths! Therefore packages is None here
        # rather, add all includes to dependencies
        packages,dir_dependencies,dir_dependency_types,dir_found_includes = self.check_files(files,None,includes_used)

        dependencies.extend(dir_dependencies)
        dependency_types.extend(dir_dependency_types)
        found_includes.extend(dir_found_includes)

    #if debug:
    #    print "Added files after checking include directories:"+" ".join([x.abspath() for x in dependencies])

    # now recursively scan the include files
    for inc in found_includes:
        if debug: print "Found include:",inc
        mystack = copy.copy(stack)
        (add_dependencies, add_dependency_types) = self.scan_verilog_file(inc,mystack,debug)
        for f,t in zip(add_dependencies,add_dependency_types):
            if not node.change_ext('.sv.out') == f:
                dependencies.append(f)
                dependency_types.append(t)

    return (dependencies,dependency_types)


