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

def verilog_scanner_task(task):
    task.generator.verilog_scanner(task.inputs[0])

@TaskGen.taskgen_method
def verilog_scanner(self,node):
    input = open(node.abspath(),'r')
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

	#print includes_used

    input.close()
    # now make use of a very cool python feature: set difference
    packages = packages_used-packages_defined
    # all dependencies will be put into this list
    dependencies = []
    # get an instance of the root node
    up = "../"
    for i in range(node.height()-1):
        up += "../"
    rootnode = node.find_dir(up)
    # loop through search paths to find the file that defines the package
    for dir in self.env['VERILOG_SEARCH_PATHS']:
        if (dir == '-INCDIR'):
            continue
        # convert dir to waf node
        pattern = re.compile("^\/")
        if not pattern.match(dir):
            dir = rootnode.ctx.srcnode.make_node(dir)
        else:
            dir = rootnode.make_node(dir)
        # get all system verilog files
        files = get_sv_files_from_include_dir(rootnode,dir)
        for file in files:
            packages_loadable = set()
            input = open(file.abspath(),'r')
            for line in input:
                m0 = re.search('package\s+(\w+);', line)
                if (m0 is not None):
                    #print "Found package: "+m0.group(1)
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
                dependencies.append(file.change_ext(file.suffix()+'.out'))

	#print dependencies
    # return dependencies
    return (dependencies,[])


