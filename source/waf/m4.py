
from waflib import Task, TaskGen, Logs, Node, Errors

@TaskGen.feature('m4')
@TaskGen.before('process_source')
def m4_prepare(self):
    inputs = self.to_nodes(getattr(self,'source',[]))
    self.source = []

    for f in inputs:
        output = f.change_ext('.preproc.sv')
        open(output.abspath(),'w').close()
        self.create_task("m4Task",f,output)

class m4Task(Task.Task):
    def run(self):
        run_str = 'm4 '+(''.join([ ' -I '+i for i in self.generator.includes]))+' ${SRC} > ${TGT}'
        (f, dvars) = Task.compile_fun(run_str, False)
        return f(self)

