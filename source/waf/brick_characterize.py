import os
from brick_characterizer.do_characterization import do_characterization
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	conf.load('brick_general')

	conf.find_program('ultrasim', var='CDS_ULTRASIM')

@TaskGen.feature('brick_characterize')
def create_brick_characterize_task(self):
    # backwards compatibility
    if not hasattr(self,'analogs'):
        self.analogs = []
    if hasattr(self,'parasitics_report'):
        self.create_task('brickCharacterizerTask',self.parasitics_report,self.output_lib_file)
    else:
        self.create_task('brickCharacterizerTask',[],self.output_lib_file)

@Task.always_run
class brickCharacterizerTask(Task.Task):
    def run(self):
        os.chdir(self.generator.bld.bldnode.abspath())
        if hasattr(self.generator,'parasitics_report'):
            self.generator.parasitics_report = self.generator.parasitics_report.abspath()
        else:
            self.generator.parasitics_report = None

        return do_characterization(
            # names
            self.generator.lib_name,
            self.generator.cell_name,
            # files
            self.generator.output_lib_file.abspath(),
            self.generator.output_netlist_file,
            # netlists
            [self.generator.model_netlist_path,self.generator.circuit_netlist_path],
            # ports
            self.generator.inputs,
            self.generator.outputs,
            self.generator.inouts,
            getattr(self.generator,'analogs',[]),
            self.generator.powers,
            self.generator.static_signals,
            self.generator.clocks,
            self.generator.input_timing_signals,
            self.generator.output_timing_signals,
            # templates
            self.generator.constraint_template,
            self.generator.delay_template,
            # logfile
            self.generator.logfile,
            # temperature
            self.generator.temperature,
            # capacitance file
            self.generator.parasitics_report,
            # flow settings
            self.generator.only_rewrite_lib_file,
            self.generator.skip_setup_hold,
            self.generator.skip_delays,
            getattr(self.generator,'use_spectre',False),
            # other stuff
            getattr(self.generator,'additional_probes',{}),
            getattr(self.generator,'default_max_transition',0.2),
        )

