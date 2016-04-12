import re
import copy
import os, logging

class CharBase(object):

    def __init__(self,temperature,use_spectre=False):
        self.__temperature = temperature
        self.rise_threshold = 0.501
        self.fall_threshold = 0.499
        self.slew_lower_rise = 0.3
        self.slew_upper_rise = 0.7
        self.slew_lower_fall = 0.3
        self.slew_upper_fall = 0.7
        self.slew_derate_factor = 0.8
        self.high_value = 1.2
        self.low_value = 0.0
        self.timing_offset = 4.0 #ns
        self.clock_period = 3.0 #ns
        self.simulation_length = 12.0 #ns
        self.epsilon = 1.e-6
        self.infinity = 1000.
        self.added_static_signals = False
        self.added_timing_signals = False
        self.powers = {'vdd': 1.2, 'gnd': 0.0}
        self.spice_output = []
        self.output_dir = 'output'
        self.include_netlists = []
        # hold static signals and their constant values
        self.static_signals = {}
        # store timing results
        self.timing_signals = {}
        self.source_signals = {}
        self.output_signals = {}
        self.use_spectre = use_spectre

        self.additional_probes = {}

        self.state = 'init'

        self.check_output_dir_exists()

    def check_output_dir_exists(self):
        if not os.path.isdir(self.output_dir):
            self.logger_info('Output directory '+self.output_dir+' not existing. Creating it.')
            os.makedirs(self.output_dir)

        if not os.path.isdir(os.path.dirname(self.output_filename)):
            self.logger_info('Output directory '+os.path.dirname(self.output_filename)+' not existing. Creating it.')
            os.makedirs(os.path.dirname(self.output_filename))

    # logger bleiben
    def logger_debug(self,text):
        """Debugging output wrapper that prepends *self.log_my_name()* to the
        output"""
        logging.debug(self.log_my_name()+' '+text)

    def logger_warning(self,text):
        """Warning output wrapper that prepends *self.log_my_name()* to the
        output"""
        logging.warning(self.log_my_name()+' '+text)

    def logger_error(self,text):
        """Error output wrapper that prepends *self.log_my_name()* to the
        output"""
        logging.error(self.log_my_name()+' '+text)

    def logger_info(self,text):
        """Info output wrapper that prepends *self.log_my_name()* to the
        output"""
        logging.info(self.log_my_name()+' '+text)

    def set_rise_threshold(self,value):
        if value > 1:
            raise Exception('rise threshold cannot be greater than 1')

        self.rise_threshold = value

    def set_fall_threshold(self,value):
        if value > 1:
            raise Exception('fall threshold cannot be greater than 1')
        self.fall_threshold = value

    def set_powers(self,values):
        self.powers = values

    def append_out(self,line):
        self.spice_output.append(line)

    def add_additional_probes(self,probes):
        self.additional_probes = probes

    def add_include_netlist(self,netlist):
        import os
        try:
            if not os.path.isfile(netlist['filename']):
                raise Exception('Netlist '+netlist['filename']+' to be included in '+self.whats_my_name()+' not found')
        except TypeError:
            if not os.path.isfile(netlist):
                raise Exception('Netlist '+netlist+' to be included in '+self.whats_my_name()+' not found')

        self.include_netlists.append(netlist)

    def add_static_signals(self,signals):
        for signal,related in self.itersignals(signals):
            if self.added_timing_signals:
                if self.timing_signals.has_key(signal) or self.source_signals.has_key(signal) or self.clocks.has_key(signal):
                    raise Exception('Static signal '+signal+' has already been defined as a timing or clock signal.')
            self.static_signals[signal] = value

        self.added_static_signals = True

    def get_rising_edges(self,signal_name):
        """Access the rising edges that have been extracted with
        *parse_print_file()*."""
        edges = None
        if not self.use_spectre:
            signal_name = signal_name.lower()
        try:
            edges = self.rising_edges[signal_name]
        except KeyError:
            try:
                edges = self.rising_edges['v('+signal_name+')']

            except KeyError:
                pass

        return edges

    def get_falling_edges(self,signal_name):
        """Access the falling edges that have been extracted with
        *parse_print_file()*."""
        edges = None
        if not self.use_spectre:
            signal_name = signal_name.lower()
        try:
            edges = self.falling_edges[signal_name]
        except KeyError:
            try:
                edges = self.falling_edges['v('+signal_name+')']
            except KeyError:
                pass

        return edges

    def write_include_netlists(self):
        for netlist in self.include_netlists:
            try:
                self.append_out('include "'+netlist['filename']+'" section='+netlist['section'])
            except TypeError:
                self.append_out('include "'+netlist+'"')

        self.append_out('')


    def generate_instance(self):
        # spectre needs an extra instantiation of the circuit
        # ultrasim is fine with only the circuit definition
        if self.use_spectre:
            self.append_out('X'+self.toplevel)
            self.append_out('''+ VDD CP VSS D Q QN''')

            # for (signal,value) in self.static_signals.iteritems():
                # self.append_out('+ '+signal)
            # for signal,value in self.timing_signals.iteritems():
                # self.append_out('+ '+signal)
            # for signal,value in self.output_signals.iteritems():
                # self.append_out('+ '+signal)

            self.append_out('+ '+self.toplevel)


    def generate_additional_probes(self):
        for probe,probe_type in self.additional_probes.iteritems():
            if probe_type == 'v' or probe_type == 'V':
                self.add_probe(probe,with_print=False)
            elif probe_type == 'i' or probe_type == 'I':
                self.add_current_probe(probe,with_print=False)
            elif probe_type == 'p' or probe_type == 'P':
                self.add_power_probe(probe,with_print=False)

    def generate_single_stat_signal_source(self,signal,value):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')
        if value == 1:
            value = str(self.high_value)
        else:
            value = str(self.low_value)

        self.append_out('+ 0.0000000e+00 '+value+'000000e+00')
        self.append_out('+ 2.4999999e-13 '+value+'000000e+00')
        self.append_out('+ 5.0000000e-09 '+value+'000000e+00)')

    def generate_static_signals(self):
        for power_name,power_value in self.powers.iteritems():
            self.append_out('V'+power_name+' '+power_name+'_ideal 0 '+str(power_value))
            self.append_out('R'+power_name+' '+power_name+'_ideal '+power_name+' 0.1')

        for (signal,value) in self.static_signals.iteritems():
            #single net
            self.generate_single_stat_signal_source(signal,value)

    def add_power_probe(self,signal,with_print=True):
        if with_print:
            self.append_out('.print p('+signal+')')
        self.append_out('.probe p('+signal+')')

    def add_current_probe(self,signal,with_print=True):
        if with_print:
            self.append_out('.print i('+signal+')')
        self.append_out('.probe i('+signal+')')

    def add_probe(self,signal,with_print=True):
        if with_print:
            self.append_out('.print v('+signal+')')
        self.append_out('.probe v('+signal+')')

    def write_header(self):
        self.append_out('* brick characterizer')
        self.append_out('simulator lang=spectre')
        self.append_out('parameters tran_tend='+str(self.simulation_length)+'000000e-09')
        self.append_out('tran tran step=1.00e-12 stop=tran_tend')
        self.append_out('simulatorOptions options temp='+str(self.__temperature))#+' tnom=27 scale=1.0 scalem=1.0')
        #self.append_out('usim_opt sim_mode=a subckt=synapse')
        #self.append_out('usim_opt sim_mode=s')
        self.write_include_netlists()
        self.append_out('')
        self.append_out('simulator lang=spice')
        self.append_out('')


    def oom(self,exp):
        if exp == 'm':
            return 1.e-3
        elif exp == 'u':
            return 1.e-6
        elif exp == 'n':
            return 1.e-9
        elif exp == 'p':
            return 1.e-12
        elif exp == 'f':
            return 1.e-15
        elif exp == 'k':
            return 1.e3
        elif exp == 'M':
            return 1.e6
        elif exp == 'G':
            return 1.e9

    def run(self):
        """Start the actual simulation for the current step using
        *subprocess.call()*."""
        import subprocess
        call = []
        if not self.use_spectre:
            call = ['ultrasim', '-f', self.get_current_filename(), '-outdir', self.output_dir, '-format', 'sst2', '-top', self.toplevel,'=log',self.get_current_logfile()]
        else:
            call = ['spectre', '-outdir', self.output_dir, '-format', 'sst2', '=log',self.get_current_logfile(), self.get_current_filename()]
        self.logger_debug(" ".join(call))
        returncode = subprocess.call(call)
        return returncode

    def get_current_filename(self):
        import os
        name,ext = os.path.splitext(self.output_filename)
        return name+ext


    def get_current_logfile(self):
        import os
        name,ext = os.path.splitext(self.get_current_filename())
        if not self.use_spectre:
            return name+'.log'
        else:
            return self.output_dir+'/'+name+'.log'

    def has_steps(self):
        if self.state == 'done':
            return 0
        else:
            return 1

    def write_spice_file(self):
        """Write the spice file for the current step. This calls::

            self.write_header()
            self.generate_static_signals()
            self.generate_timing_signals()
            self.generate_additional_probes()
            self.generate_instance()

        """

        self.write_header()
        self.generate_static_signals()
        self.generate_timing_signals()
        self.generate_additional_probes()
        self.generate_instance()

        self.logger_debug("Writing to filename "+self.get_current_filename())

        f = open(self.get_current_filename(),'w')
        for line in self.spice_output:
            f.write(line+'\n')
        f.close()

        self.spice_output = []


    def get_printfile_name(self):
        import os
        if not self.use_spectre:
            return self.output_dir+'/'+os.path.splitext(os.path.basename(self.get_current_filename()))[0]+'.print0'
        else:
            return self.output_dir+'/'+os.path.splitext(os.path.basename(self.get_current_filename()))[0]+'.print'

    def itersignals(self,signals,eval_index_expression=False):
        """This is a generator function that iterates over the signals in the
        input dict (*signals*). The input dict can contain multiple signals or
        buses. For buses the individual signal bits will be yielded. If
        eval_index_expression is set to True, the item at position 1 of the
        list that is associated with each signals is checked for index
        expressions.

        It can be used like::

            for signal in filter(function,self.itersignals(signals)):
                # do something

        """
        # The following loop used to appear often in this program.
        # The way I chose to generalize it was to make a generator out of it.
        # So now it can be used like
        # for signal in filter(function,self.itersignals(signals)):
        #     # do something

        assert type(signals) is dict
        for name,related in signals.iteritems():
            bus = re.compile(r"\[(\d+):(\d+)\]")
            m = bus.search(name)
            if m:
                smaller = int(m.group(1))
                larger = int(m.group(2))
                if smaller >= larger:
                    larger,smaller = smaller,larger

                for index in range(smaller,larger+1):
                    cur_sig = re.sub(r"\[\d+:\d+\]","["+str(index)+"]",name)
                    cur_rel = copy.copy(related)
                    if eval_index_expression is True:
                        tests = []
                        tests.append(re.compile(r"=(index)="))
                        tests.append(re.compile(r"=([\*\d\%\+\/\-]*index[\*\d\%\+\/\-]*)="))

                        match = None
                        for test in tests:
                            match = test.search(cur_rel[1])
                            while match:
                                evaluated_index = int(eval(match.group(1)))
                                cur_rel[1] = test.sub(str(evaluated_index),
                                                     cur_rel[1], count=1)
                                match = test.search(cur_rel[1])

                    yield cur_sig,cur_rel

            else:
                yield name,related


    def set_initial_condition(self,signal_name,value):
        self.append_out('.IC V('+signal_name+')='+str(value))
        self.append_out('.NODESET V('+signal_name+')='+str(value))

    def _add_edge(self, at, tran, from_level, to_level):
        """Append two lines to the spice file output, the add an edge to a
        piecewise linear source. Both lines start with a '+' sign (spice
        multi-line statements). *at* and *tran* must be given in nano seconds.
        *from_level* and *to_level* in volt or ampere."""

        self.append_out('+ '+str(at-tran*0.5)+'e-9 '+str(from_level)+'e+00')
        self.append_out('+ '+str(at+tran*0.5)+'e-09 '+str(to_level)+'e+00')

    def add_output_rise_edge(self, at, tran):
        self._add_edge(at, tran, self.low_value, self.high_value)

    def add_output_fall_edge(self, at, tran):
        self._add_edge(at, tran, self.high_value, self.low_value)

