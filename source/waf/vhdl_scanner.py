import re,os

# ---------------------
# VHDL scanner methods
# ---------------------

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
        pattern = re.compile("^\/")
        if not pattern.match(dir):
            dir = rootnode.ctx.srcnode.make_node(dir)
        else:
            dir = rootnode.make_node(dir)
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

