
from waflib import Task, TaskGen, Logs, Node, Errors

def configure(cfg):
    cfg.find_program('m4', var='M4')

@TaskGen.feature('m4')
@TaskGen.before('process_source')
def m4_prepare(self):

    for f in self.to_nodes(getattr(self,'source',[])):
        output = f.change_ext('.preproc'+f.suffix())
        open(output.abspath(),'a').close()
        self.create_task("m4Task",f,output)

    self.source = []

@TaskGen.taskgen_method
def get_preprocessed_outputs(self):
    output = []
    for f in self.to_nodes(getattr(self,'source',[])):
        output.append(f.change_ext('.preproc'+f.suffix()))
        open(output[-1].abspath(),'a').close()

    return output

class m4Task(Task.Task):
    vars = ['M4']

    def run(self):
        run_str = '${M4} '+(''.join([ ' -I '+i for i in self.generator.includes]))+' ${SRC} > ${TGT}'
        (f, dvars) = Task.compile_fun(run_str, False)
        return f(self)

