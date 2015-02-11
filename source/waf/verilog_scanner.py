import re,os,copy
from waflib import TaskGen, Logs, Node

# --------------------------------
# Verilog and VHDL scanner methods
# --------------------------------


def check_files(files,debug=False):
    packages_used = {}
    packages_defined = {}
    includes_used = {}
    nodes = {}

    for file in files:
        leaf = Node.split_path(file.abspath())[-1]
        nodes[leaf] = file
        # This is the basic check, that looks in the current file for:
        #  - packages defined
        #  - packages used/imported
        #  - files included
        with open(file.abspath(),'r') as input:
            packages_used[leaf] = set()
            packages_defined[leaf] = set()
            includes_used[leaf] = []
            if debug:
                print "Processing file:" + node.abspath()
            # look for used packages and packages that are defined in the input file
            for line in input:
                # Poor man's comment detection
                if line.find('//') == 0:
                    continue
                m0 = re.search('package\s+(\w+);', line)
                m1 = re.search('import\s+(\w+)[\s:]+', line)
                m2 = re.search('\W(\w+)::', line)
                m3 = re.search('`include\s+"([\w\.]+)"', line)
                if (m0 is not None):
                    packages_defined[leaf].add(m0.group(1))
                if (m1 is not None):
                    packages_used[leaf].add(m1.group(1))
                if (m2 is not None):
                    packages_used[leaf].add(m2.group(1))
                if (m3 is not None):
                    includes_used[leaf].append(m3.group(1))

            if debug:
                print "Packages used:"+" ".join(packages_used[leaf])
                print "Packages defined:"+" ".join(packages_defined[leaf])
                print "Includes defined:"+" ".join(includes_used[leaf])

    return nodes, packages_used, packages_defined, includes_used


def get_sv_files_from_include_dir(rootnode,dir):
    content = dir.ant_glob("*.sv")
    content.extend(dir.ant_glob("*.svh"))
    content.extend(dir.ant_glob("*.v"))
    return content

def get_sv_files_from_include_dirs(inputs,dirs):
    # get an instance of the root node
    up = "../"
    for i in range(inputs[0].height()-1):
        up += "../"
    rootnode = inputs[0].find_dir(up)
    # declare cache
    cache = {'nodes':{},'packages_used':{},'packages_defined':{},'includes_used':{}}
    # loop through search paths to find the file that defines the package
    for dir in dirs:
        # get all system verilog files
        files = get_sv_files_from_include_dir(rootnode,dir)
        # don't look for packages in search paths! Therefore packages is None here
        # rather, add all includes to dependencies
        nodes,packages_used,packages_defined,includes_used = check_files(files)

        cache['nodes'] = dict(cache['nodes'].items() + nodes.items())
        cache['packages_used'] = dict(cache['packages_used'].items() + packages_used.items())
        cache['packages_defined'] = dict(cache['packages_defined'].items() + packages_defined.items())
        cache['includes_used'] = dict(cache['includes_used'].items() + includes_used.items())

    nodes,packages_used,packages_defined,includes_used = check_files(inputs)

    cache['nodes'] = dict(cache['nodes'].items() + nodes.items())
    cache['packages_used'] = dict(cache['packages_used'].items() + packages_used.items())
    cache['packages_defined'] = dict(cache['packages_defined'].items() + packages_defined.items())
    cache['includes_used'] = dict(cache['includes_used'].items() + includes_used.items())


    return cache

def add_include_deps(cache,includes):
    ret_deps = []
    for inc in includes:
        # add inc to current deps
        try:
            ret_deps.append(cache['nodes'][inc])
        except KeyError:
            Logs.warn('Included file '+inc+' not found in search paths.')

        try:
            ret_deps.extend(add_include_deps(cache,cache['includes_used'][inc]))
        except KeyError:
            Logs.warn('Included file '+inc+' not found in search paths.')

    return ret_deps

def scan_verilog_file(node,cache,debug=False):
    leaf = Node.split_path(node.abspath())[-1]

    #if node.abspath() in stack:
    #    raise RuntimeError("You have an include loop in your files, you should fix that. Package and include order detection? Not gonna happen!\nFile "+node.abspath()+" included by\n\t"+"\n\t".join(stack))
    #stack.append(node.abspath())

    deps = []
    asdditionals = []

    # check whether external packages are referenced in this file
    packages_missing = cache['packages_used'][leaf] - cache['packages_defined'][leaf]
    for pak in packages_missing:
        package_found = False
        for f,packages in cache['packages_defined'].iteritems():
            if pak in packages:
                package_found = True
                deps.append(cache['nodes'][f])

        if not package_found:
            pass

    # check includes
    deps.extend(add_include_deps(cache,cache['includes_used'][leaf]))


    if debug:
        print node,[x.abspath() for x in deps]
    return (deps,[])


def scan_verilog_task(task):
    #print "Scanning Task "+str(task)
    #print "Includes: "+" ".join([x.abspath() for x in getattr(task.generator,'verilog_search_paths',[])])
	# create a database of all packages used and defined in all .sv files in all incdirs
	# this will later be used in the scanner for the individual task sources
    cache = get_sv_files_from_include_dirs(task.inputs,getattr(task.generator,'verilog_search_paths',[]))

    ret = ([],[])
    debug = False
    for inp in task.inputs:
        #DELME
        if Node.split_path(inp.abspath())[-1] == 'tb_top_miniasic_0.sv':
            #print inp.abspath()
            #debug = True
            pass
        #END DELME
        new_dep = scan_verilog_file(inp,cache,debug)
        if debug:
            print new_dep
        ret[0].extend(new_dep[0])
        ret[1].extend(new_dep[1])

    return ret
