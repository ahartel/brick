import os, logging

class CharBase(object):

    def __init__(self,use_spectre=False):
        self.rise_threshold = 0.501
        self.fall_threshold = 0.499
        self.high_value = 1.2
        self.low_value = 0.0
        self.timing_offset = 4.0 #ns
        self.clock_period = 2.0 #ns
        self.simulation_length = 10.0 #ns
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
        logging.debug(self.log_my_name()+' '+text)

    def logger_warning(self,text):
        logging.warning(self.log_my_name()+' '+text)

    def logger_error(self,text):
        logging.error(self.log_my_name()+' '+text)

    def logger_info(self,text):
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
        if not os.path.isfile(netlist):
            raise Exception('Netlist '+netlist+' to be included in '+self.whats_my_name()+' not found')

        self.include_netlists.append(netlist)

    def get_rising_edges(self,signal_name):
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
            self.append_out('.include '+netlist+'')
        self.append_out('')

    def add_static_signals(self,signals):
        import re
        for name,value in signals.iteritems():
            bus = re.compile(r"\[(\d+):(\d+)\]")
            m = bus.search(name)
            if m:
                smaller = int(m.group(1))
                larger = int(m.group(2))
                if smaller >= larger:
                    larger,smaller = smaller,larger

                for index in range(smaller,larger+1):
                    cur_sig = re.sub(r"\[\d+:\d+\]","["+str(index)+"]",name)
                    self.static_signals[cur_sig] = value
                    if self.added_timing_signals:
                        if self.timing_signals.has_key(cur_sig) or self.source_signals.has_key(name) or self.clocks.has_key(cur_sig):
                            raise Exception('Static signal '+cur_sig+' has already been defined as a timing or clock signal.')

            else:
                self.static_signals[name] = value
                if self.added_timing_signals:
                    if self.timing_signals.has_key(name) or self.source_signals.has_key(name) or self.clocks.has_key(name):
                        raise Exception('Static signal '+name+' has already been defined as a timing or clock signal.')

        self.added_static_signals = True

    def generate_instance(self):
        if self.use_spectre:
            self.append_out('X'+self.toplevel)
            self.append_out('''+ vdd gnd en clk_int w_conf[7] w_conf[5] w_conf[3] w_conf[1] wen
    + bl_w w_conf[6] w_conf[4] w_conf[2] w_conf[0] write pc_confb[3] bl_pc_out
    + pc_confb[2] pc_confb[1] pc_confb[0] str clk bl_pc_in clk_intb pc sense
    + write_en w_a[0] w_ab[0] w_ab[1] w_a[1] w_a[2] w_ab[2] w_ab[3] w_a[3] w_a[4]
    + w_ab[4] w_ab[5] w_a[5] w_a[6] w_ab[6] addr[5] addr[0] addr[1] addr[3] addr[2]
    + addr[4] addr[6]''')

            #for (signal,value) in self.static_signals.iteritems():
            #    self.append_out('+ '+signal)
            #for signal,value in self.timing_signals.iteritems():
            #    self.append_out('+ '+signal)
            #for signal,value in self.output_filename.iteritems():
            #    self.append_out('+ '+signal)

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
        import re
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
        self.append_out('simulatorOptions options temp=27 tnom=27 scale=1.0 scalem=1.0')
        #self.append_out('usim_opt sim_mode=a subckt=synapse')
        #self.append_out('usim_opt sim_mode=s')
        self.append_out('')
        self.append_out('simulator lang=spice')
        self.append_out('')
        self.write_include_netlists()


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
