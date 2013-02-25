import logging

class SimulationRun:
    def __init__(self,toplevel,output_filename):

        self.toplevel = toplevel
        self.output_filename = output_filename
        self.spice_output = []
        self.include_netlists = []
        # hold static signals and their constant values
        self.static_signals = {}
        # store timing results
        self.timing_signals = {}
        # store probe signals and their related inputs
        self.probe_signals = {}
        # store unateness of probe signals
        self.probe_signal_directions = {}
        # store clock signals and their edge type
        self.clocks = {}
        # store which clock belongs to which input signal
        self.signal_to_clock = {}
        self.powers = {'vdd': 1.2, 'gnd': 0.0}
        self.output_dir = 'output'
        self.rising_edges = {}
        self.falling_edges = {}

        self.state = 'init'
        self.state_cnt = 0
        self.delays = { }
        self.setups = { }
        self.holds = { }

        self.initial_delay = 0.4 #ns
        self.initial_stepsize = 0.2 #ns
        self.current_delay = {}
        self.current_stepsize = {}
        self.lower_th = {}
        self.upper_th = {}
        self.direction = {}

        self.infinity = 1000.
        self.clock_rise_time = 0.1 #ns
        self.signal_rise_time = 0.1 #ns
        self.point_of_failure = 1.1 # 10 percent of delay
        self.rise_threshold = 0.501
        self.fall_threshold = 0.499
        self.high_value = 1.2
        self.low_value = 0.0
        self.timing_offset = 4.0 #ns
        self.simulation_length = 10.0 #ns
        self.max_setup_steps = 9
        self.max_hold_steps = 9
        self.epsilon = 1.e-6

        self.added_static_signals = False
        self.added_timing_signals = False

        # logger bleiben
        #self.logger = logging.getLogger('SetupAndHold')
        #self.logger.setLevel(logging.DEBUG)
        #ch = logging.FileHandler('./logfiles/'+self.whats_my_name()+'.log')
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        #self.logger.addHandler(ch)

    def logger_debug(self,text):
        logging.debug(self.whats_my_name()+' '+text)

    def whats_my_name(self):
        return 'SimulationRun_clk'+str(self.clock_rise_time)+'_sig'+str(self.signal_rise_time)

    def get_holds(self):
        return self.holds

    def get_setups(self):
        return self.setups

    def get_clock_rise_time(self):
        return self.clock_rise_time

    def set_clock_rise_time(self,value):
        self.clock_rise_time = value

    def get_signal_rise_time(self):
        return self.signal_rise_time

    def set_signal_rise_time(self,value):
        self.signal_rise_time = value

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

    def add_static_signals(self,signals):
        if self.added_timing_signals:
            for name in signals.iterkeys():
                if self.timing_signals.has_key(name) or self.clocks.has_key(name):
                    raise Exception('Static signal '+name+' has already been defined as a timing or clock signal.')

        self.static_signals = signals
        self.added_static_signals = True

    def generate_single_signal(self,signal,value):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')
        if value == 1:
            value = str(self.high_value)
        else:
            value = str(self.low_value)

        self.append_out('+ 0.0000000e+00 '+value+'000000e+00')
        self.append_out('+ 2.4999999e-13 '+value+'000000e+00')
        self.append_out('+ 5.0000000e-09 '+value+'000000e+00)')

    def generate_single_edge(self,signal,rise_time,start_delay,edge_type):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')

        if self.state == 'delay':
            start_time = self.timing_offset - start_delay
        elif self.state == 'setup':
            start_time = self.timing_offset - start_delay
        elif self.state == 'hold':
            start_time = self.timing_offset + start_delay
            if edge_type == 'R':
                edge_type = 'F'
            else:
                edge_type = 'R'

        if edge_type == 'R':
            self.append_out('+ 0.0000000e+00 0.0000000e+00')
            self.append_out('+ '+str(start_time)+'e-9 0.0000000e+00')
            self.append_out('+ '+str(start_time+rise_time)+'000000e-09 '+str(self.high_value)+'000000e+00)')
        else:
            self.append_out('+ 0.0000000e+00 '+str(self.high_value)+'000000e+00')
            self.append_out('+ '+str(start_time)+'e-9 '+str(self.high_value)+'000000e+00')
            self.append_out('+ '+str(start_time+rise_time)+'000000e-09 '+str(self.low_value)+'000000e+00)')

    def generate_two_edges(self,signal,transition_time,rising_delay,falling_delay):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')

        if self.state == 'delay':
            start_time = self.timing_offset - rising_delay
            start_time_2 = self.timing_offset*2 - falling_delay
            first_value = self.low_value
            second_value = self.high_value
        elif self.state == 'setup':
            start_time = self.timing_offset - rising_delay
            start_time_2 = self.timing_offset*2 - falling_delay
            first_value = self.low_value
            second_value = self.high_value
        elif self.state == 'hold':
            start_time = self.timing_offset + rising_delay
            start_time_2 = self.timing_offset*2 + falling_delay
            first_value = self.high_value
            second_value = self.low_value

        self.append_out('+ 0.0000000e+00 '+str(first_value)+'e+00')
        self.append_out('+ '+str(start_time)+'e-9 '+str(first_value)+'e+0')
        self.append_out('+ '+str(start_time+transition_time)+'e-09 '+str(second_value)+'e+00)')
        self.append_out('+ '+str(start_time_2)+'e-9 '+str(second_value)+'e+00')
        self.append_out('+ '+str(start_time_2+transition_time)+'e-09 '+str(first_value)+'e+00)')

    def generate_clock_edge(self,name,direction):
        self.append_out('V'+name+' '+name+' 0 pwl(')
        if direction == 'R':
            self.append_out('+ 0.0000000e+00 0.0000000e+00')
            self.append_out('+ '+str(self.timing_offset)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*1.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*1.5 + self.clock_rise_time)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*2)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*2 + self.clock_rise_time)+'e-09 '+str(self.high_value))
        else:
            self.append_out('+ 0.0000000e+00 '+str(self.high_value)+'000000e+00')
            self.append_out('+ '+str(self.timing_offset)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*1.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*1.5 + self.clock_rise_time)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*2)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*2 + self.clock_rise_time)+'e-09 '+str(self.low_value))

    def generate_static_signals(self):
        import re
        for power_name,power_value in self.powers.iteritems():
            self.append_out('V'+power_name+' '+power_name+' 0 '+str(power_value))

        for (signal,value) in self.static_signals.iteritems():
            #single net
            self.generate_single_signal(signal,value)

    def add_probe(self,signal):
        self.append_out('.print v('+signal+')')
        self.append_out('.probe v('+signal+')')

    #def get_current_input_delay(self):
    #    if self.state == 'delay':
    #        return self.delay_steps[self.state_cnt]
    #    elif self.state == 'setup':
    #        return self.setup_steps[self.state_cnt]
    #    elif self.state == 'hold':
    #        return self.hold_steps[self.state_cnt]

    def generate_timing_signals(self):
        import re

        for name,direction in self.clocks.iteritems():
            self.generate_clock_edge(name,direction)
            self.add_probe(name)

        for signal in self.timing_signals.iterkeys():
            self.generate_two_edges(signal,self.signal_rise_time,self.current_delay[signal][0],self.current_delay[signal][1])
            self.logger_debug("Generating edge for "+signal+" with rising delay "+str(self.current_delay[signal][0])+ " and falling delay "+str(self.current_delay[signal][1]))
            self.add_probe(signal)

        for signal in self.probe_signals.iterkeys():
            self.add_probe(signal)

    def get_current_filename(self):
        import os
        name,ext = os.path.splitext(self.output_filename)
        return name+'_clk'+str(self.clock_rise_time)+'_sig'+str(self.signal_rise_time)+'_'+self.state+'_'+str(self.state_cnt)+ext

    def get_current_logfile(self):
        import os
        name,ext = os.path.splitext(self.get_current_filename())
        return name+'.log'

    def write_spice_file(self):

        self.append_out('* brick characterizer')
        self.write_include_netlists()
        self.write_header()
        self.generate_static_signals()
        self.generate_timing_signals()

        self.logger_debug("Writing to filename "+self.get_current_filename())

        f = open(self.get_current_filename(),'w')
        for line in self.spice_output:
            f.write(line+'\n')
        f.close()

        self.spice_output = []

    def add_include_netlist(self,netlist):
        import os
        if not os.path.isfile(netlist):
            raise Exception('include-netlist not found')

        self.include_netlists.append(netlist)

    def add_timing_signals(self,clocks,tim_sig):
        import re
        #import pprint
        #pp = pprint.PrettyPrinter(indent=4)

        self.clocks = clocks

        if self.added_static_signals:
            for name in clocks.iterkeys():
                if self.static_signals.has_key(name):
                    raise Exception('Clock signal '+name+' has already been defined as a static signal.')

        for sig,related in tim_sig.iteritems():
            bus = re.compile(r"\[(\d+):(\d+)\]")
            m = bus.search(sig)
            if m:
                smaller = int(m.group(1))
                larger = int(m.group(2))
                if smaller >= larger:
                    larger,smaller = smaller,larger

                for index in range(smaller,larger+1):
                    cur_sig = re.sub(r"\[\d+:\d+\]","["+str(index)+"]",sig)
                    cur_probe = related[1]
                    tests = []
                    tests.append(re.compile(r"=(index)="))
                    tests.append(re.compile(r"=(index[\*\d\%\+\/\-]+)="))

                    match = None
                    for test in tests:
                        match = test.search(related[1])
                        while match:
                            cur_probe = test.sub(str(int(eval(match.group(1)))),cur_probe,count=1)
                            match = test.search(cur_probe)

                    self.timing_signals[cur_sig] = {}
                    self.current_delay[cur_sig] = [self.initial_delay,self.initial_delay]
                    self.current_stepsize[cur_sig] = [self.initial_stepsize,self.initial_stepsize]
                    self.direction[cur_sig] = [-1.,-1.]
                    self.upper_th[cur_sig] = [self.infinity,self.infinity]
                    self.signal_to_clock[cur_sig] = related[0]
                    self.probe_signals[cur_probe] = cur_sig
                    self.probe_signal_directions[cur_probe] = related[2]

            else:
                if self.added_static_signals:
                    if self.static_signals.has_key(name):
                        raise Exception('Timing signal '+name+' has already been defined as a static signal.')

                self.timing_signals[sig] = {}
                self.current_delay[sig] = [self.initial_delay,self.initial_delay]
                self.current_stepsize[sig] = [self.initial_stepsize,self.initial_stepsize]
                self.direction[sig] = [-1.,-1.]
                self.upper_th[sig] = [self.infinity,self.infinity]
                self.signal_to_clock[sig] = related[0]
                self.probe_signals[related[1]] = sig
                self.probe_signal_directions[related[1]] = related[2]


        self.added_timing_signals = True

    def write_header(self):
        self.append_out('.param tran_tend='+str(self.simulation_length)+'000000e-09')
        self.append_out('.tran 1.00e-12 \'tran_tend\'')
        self.append_out('')

    def write_include_netlists(self):
        for netlist in self.include_netlists:
            self.append_out('.include '+netlist+'')
        self.append_out('')

    def has_steps(self):
        if self.state == 'done':
            return 0
        else:
            return 1

    def next_step(self):
        if self.state == 'init':
            self.state = 'delay'
            self.state_cnt = 0
            self.write_spice_file()
            self.run()
            self.check_timing()

            self.state = 'setup'
            self.state_cnt = 0

        elif self.state == 'setup':
            self.write_spice_file()
            self.run()
            self.check_timing()

            if self.state_cnt == self.max_setup_steps-1:
                self.state_cnt = 0
                self.state = 'hold'
                for sig in self.timing_signals.iterkeys():

                    self.setups[sig] = [self.lower_th[sig][0]+(self.upper_th[sig][0]-self.lower_th[sig][0])/2.,self.lower_th[sig][1]+(self.upper_th[sig][1] - self.lower_th[sig][1])/2.]
                    self.logger_debug("Rise Setup time for signal "+sig+": "+str(self.setups[sig][0]))
                    self.logger_debug("Fall Setup time for signal "+sig+": "+str(self.setups[sig][1]))
                    # reset
                    neg_inf = -1.*self.infinity
                    self.lower_th[sig] = [neg_inf,neg_inf]
                    self.upper_th[sig] = [self.infinity,self.infinity]
                    self.current_delay[sig] = [self.initial_delay,self.initial_delay]
                    self.current_stepsize[sig] = [self.initial_stepsize,self.initial_stepsize]
                    self.current_delay[sig] = [self.initial_delay,self.initial_delay]
                    self.current_stepsize[sig] = [self.initial_stepsize,self.initial_stepsize]
                    self.direction[sig] = [-1.,-1.]

            else:
                self.state_cnt += 1

        elif self.state == 'hold':
            self.write_spice_file()
            self.run()
            self.check_timing()

            if self.state_cnt == self.max_hold_steps-1:
                self.state = 'done'
                self.state_cnt = 0
                for sig in self.timing_signals.iterkeys():

                    self.holds[sig] = [self.lower_th[sig][0]+(self.upper_th[sig][0]-self.lower_th[sig][0])/2.,self.lower_th[sig][0]+(self.upper_th[sig][1] - self.lower_th[sig][1])/2.]
                    self.logger_debug("Rise Hold time for signal "+sig+": "+str(self.holds[sig][0]))
                    self.logger_debug("Fall Hold time for signal "+sig+": "+str(self.holds[sig][1]))
                    # reset
                    neg_inf = -1.*self.infinity
                    self.lower_th[sig] = [neg_inf,neg_inf]
                    self.upper_th[sig] = [self.infinity,self.infinity]
                    self.current_delay[sig] = [self.initial_delay,self.initial_delay]
                    self.current_stepsize[sig] = [self.initial_stepsize,self.initial_stepsize]
                    self.current_delay[sig] = [self.initial_delay,self.initial_delay]
                    self.current_stepsize[sig] = [self.initial_stepsize,self.initial_stepsize]
                    self.direction[sig] = [-1.,-1.]
            else:
                self.state_cnt += 1

        else:
            self.state = 'done'
            return 0

    def run(self):
        import subprocess
        call = ['ultrasim', '-f', self.get_current_filename(), '-outdir', self.output_dir, '-format', 'sst2', '-top', self.toplevel,'=log',self.get_current_logfile()]
        self.logger_debug(" ".join(call))
        process = subprocess.Popen(call,stdout=subprocess.PIPE)
        process.wait()

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


    def check_timing(self):
        # parse result file
        # after this step, all edges are identified
        self.parse_print_file()
        # find clock edge
        clock_edges = {}
        for clock_name, clock_dir in self.clocks.iteritems():
            if not clock_edges.has_key(clock_name):
                clock_edges[clock_name] = []
            if (clock_dir == 'R'):
                clock_edges[clock_name] = self.rising_edges[clock_name]
                self.logger_debug( "Rising edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))
            else:
                clock_edges[clock_name] = self.falling_edges[clock_name]
                self.logger_debug( "Falling edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))

        for signal,related in self.probe_signals.iteritems():
            delta_t = [0,0]
            signal_lc = signal.lower()
            if self.probe_signal_directions[signal] == 'positive_unate':
                if self.rising_edges.has_key(signal_lc) and len(self.rising_edges[signal_lc]) > 0:
                    delta_t[0] = self.rising_edges[signal_lc].pop(0)
                    self.logger_debug( "Rising edge for "+signal+" at "+str(delta_t[0]))
                    delta_t[0] -= clock_edges[self.signal_to_clock[related]][0]
                    if delta_t[0] > self.timing_offset*1.e-9:
                        self.logger_debug("Rising edge for signal "+signal+" too far away from clock edge")
                        delta_t[0] = self.infinity
                    else:
                        self.logger_debug( "Delay: "+str(delta_t[0]))
                else:
                    self.logger_debug("Rising edge for signal "+signal+" not found but expected")
                    delta_t[0] = self.infinity

                if self.falling_edges.has_key(signal_lc) and len(self.falling_edges[signal_lc]) > 0:
                    delta_t[1] = self.falling_edges[signal_lc].pop(0)
                    self.logger_debug( "Falling edge for "+signal+" at "+str(delta_t[1]))
                    delta_t[1] -= clock_edges[self.signal_to_clock[related]][1]
                    if delta_t[1] > self.timing_offset*1.e-9:
                        self.logger_debug("Falling edge for signal "+signal+" too far away from clock edge")
                        delta_t[1] = self.infinity
                    else:
                        self.logger_debug( "Delay: "+str(delta_t[1]))
                else:
                    self.logger_debug("Falling edge for signal "+signal+" not found but expected")
                    delta_t[1] = self.infinity
            elif self.probe_signal_directions[signal] == 'negative_unate':
                if self.falling_edges.has_key(signal_lc) and len(self.falling_edges[signal_lc]) > 0:
                    delta_t[1] = self.falling_edges[signal_lc].pop(0)
                    self.logger_debug( "Falling edge for "+signal+" at "+str(delta_t[1]))
                    delta_t[1] -= clock_edges[self.signal_to_clock[related]][0]
                    if delta_t[1] > self.timing_offset*1.e-9:
                        self.logger_debug("Falling edge for signal "+signal+" too far away from clock edge")
                        delta_t[1] = self.infinity
                    else:
                        self.logger_debug( "Delay: "+str(delta_t[1]))
                else:
                    self.logger_debug("Falling edge for signal "+signal+" not found but expected")
                    delta_t[1] = self.infinity

                if self.rising_edges.has_key(signal_lc) and len(self.rising_edges[signal_lc]) > 0:
                    delta_t[0] = self.rising_edges[signal_lc].pop(0)
                    self.logger_debug( "Rising edge for "+signal+" at "+str(delta_t[0]))
                    delta_t[0] -= clock_edges[self.signal_to_clock[related]][1]
                    if delta_t[0] > self.timing_offset*1.e-9:
                        self.logger_debug("Rising edge for signal "+signal+" too far away from clock edge")
                        delta_t[0] = self.infinity
                    else:
                        self.logger_debug( "Delay: "+str(delta_t[0]) )
                else:
                    self.logger_debug("Rising edge for signal "+signal+" not found but expected")
                    delta_t[0] = self.infinity


            #
            # the following block implements
            # a binary search algorithm that
            # tries to look for the setup and
            # hold time of a signal
            #
            if self.state == 'delay':
                self.delays[related] = delta_t
                self.lower_th[related] = self.current_delay[related]
                self.current_delay[related][0] += self.direction[related][0] * self.current_stepsize[related][0]
                self.current_delay[related][1] += self.direction[related][1] * self.current_stepsize[related][1]
            elif self.state == 'setup' or self.state == 'hold':
                # iterate over rising and falling constraint
                for edge_type in [0,1]:
                    if self.direction[related][edge_type] < 0 and delta_t[edge_type] < self.delays[related][edge_type]*self.point_of_failure:
                        self.lower_th[related][edge_type] = self.current_delay[related][edge_type]
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
                        # don't check points twice, step back a bit instead
                        if abs(self.current_delay[related][edge_type] - self.upper_th[related][edge_type]) < self.epsilon:
                            self.logger_debug("Hit upper threshold")
                            self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                            self.current_delay[related][edge_type] -= self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

                    elif self.direction[related][edge_type] < 0 and delta_t[edge_type] > self.delays[related][edge_type]*self.point_of_failure:
                        self.upper_th[related][edge_type] = self.current_delay[related][edge_type]
                        self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                        self.direction[related][edge_type] = +1.
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
                    elif self.direction[related][edge_type] > 0 and delta_t[edge_type] < self.delays[related][edge_type]*self.point_of_failure:
                        self.lower_th[related][edge_type] = self.current_delay[related][edge_type]
                        self.direction[related][edge_type] = -1.
                        self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
                    elif self.direction[related][edge_type] > 0 and delta_t[edge_type] > self.delays[related][edge_type]*self.point_of_failure:
                        self.upper_th[related][edge_type] = self.current_delay[related][edge_type]
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
                        # don't check points twice, step back a bit instead
                        if abs(self.current_delay[related][edge_type] - self.lower_th[related][edge_type]) < self.epsilon:
                            self.logger_debug("Hit lower threshold")
                            self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                            self.current_delay[related][edge_type] -= self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

            #elif self.state == 'hold':
            #    self.holds[self.hold_steps[self.state_cnt]] = delta_t

    def get_printfile_name(self):
        import os
        return self.output_dir+'/'+os.path.splitext(os.path.basename(self.get_current_filename()))[0]+'.print0'


    def parse_print_file(self):
        import subprocess
        call = ['python', './brick_characterizer/parse_print_file.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold)]
        #self.logger_debug(" ".join(call))
        process = subprocess.Popen(call,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        process.wait()

        import pickle
        with open(self.get_printfile_name()+'_rising') as input:
            self.rising_edges = pickle.load(input)
        with open(self.get_printfile_name()+'_falling') as input:
            self.falling_edges = pickle.load(input)


