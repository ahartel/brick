def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
            return ''.join(rc)

def getTextNodeValue(tree,nodeName):
    return getText(tree.getElementsByTagName(nodeName)[0].childNodes).encode('ascii')


#
# Tasks
#

def rtl_compiler(task):
    TCLscript = task.inputs[0].abspath()
    logFile = task.outputs[1].abspath()
    cmd = 'rc -64 -f %s -overwrite -logfile %s' % (TCLscript,logFile)
    return task.exec_command(cmd)

def genLEF(task):
    mainSkillScript = task.inputs[0].abspath()
    logFile = task.outputs[1].abspath()
    cmd = 'abstract -hi -nogui -replay %s -log %s' % (mainSkillScript,logFile)
    return task.exec_command(cmd)

def genDB(task):
    cmd = 'dc_shell-t -f ../source/tcl/lib2db.tcl'
    return task.exec_command(cmd)

def createCdsLibFile(task):
    src = task.inputs[0].abspath()
    tgt = task.outputs[0].abspath()
    cmd = "echo 'INCLUDE %s' > %s" % (src,tgt)
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

