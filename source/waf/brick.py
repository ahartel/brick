import re,os

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
            return ''.join(rc)

def getTextNodeValue(tree,nodeName):
    return getText(tree.getElementsByTagName(nodeName)[0].childNodes).encode('ascii')

def getTextNodeAsList(context,tree,nodeName):
    textnode = getTextNodeValue(tree,nodeName)
    # remove spaces and line breaks
    textnode = textnode.replace(" ","")
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
    # replace env variables
    m = re.search('(?<=\$)(\w+)', replacestring)
    if m:
        for group in m.groups():
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

#
# Tasks
#

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
    print test
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
    cmd = 'perl ../source/perl/verilog2lib.pl %s %s' % (verilogFile,libFile)
    return task.exec_command(cmd)

