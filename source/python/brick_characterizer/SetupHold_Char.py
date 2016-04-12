from copy import copy
from timingsignal import SetupHoldTimingSignal
from brick_characterizer.CharBase import CharBase

# IMPORTANT NOTE: according to Bhasker & Chadha (page 64), the
# rise_constraint table in setup or hold constraints gives the
# timings for the rising edge of the input pin. Accordingly,
# the fall_constraint table describes the timing for the falling
# edge transition
# This fact has to be taken special care of when returning the
# setup and hold timing values for negative_unate signals!

class SetupHold_Char(CharBase):
    def __init__(self,toplevel,output_filename,temperature,output_cap,
                 use_spectre=False):
        self.toplevel = toplevel
        self.output_filename = output_filename
        # store probe signals and their related inputs
        self.probe_signals = {}
        # store unateness of probe signals
        self.probe_signal_directions = {}
        # store clock signals and their edge type
        self.clocks = {}
        # store which clock belongs to which input signal
        self.signal_to_clock = {}
        self.rising_edges = {}
        self.falling_edges = {}

        self.state_cnt = 0
        self.delays = { }
        self.setups = { }
        self.holds = { }

        self.output_capacitance = output_cap
        self.initial_delay = 0.5 #ns
        self.initial_stepsize = 0.25 #ns
        self.current_delay = {}
        self.current_stepsize = {}
        self.lower_th = {}
        self.upper_th = {}
        self.direction = {}

        self.clock_rise_time = 0.1 #ns
        self.signal_rise_time = 0.1 #ns
        self.point_of_failure = 1.1 # 10 percent of delay

        self.max_setup_steps = 15
        self.max_hold_steps = 15

        super(SetupHold_Char,self).__init__(temperature,use_spectre)

    def whats_my_name(self):
        name = 'SetupHold_Char_clk'+str(self.get_clock_rise_time())
        name += '_sig'+str(self.get_signal_rise_time())
        return name

    def log_my_name(self):
        name = self.state+'\tc'+str(self.get_clock_rise_time())
        name += '\ts'+str(self.get_signal_rise_time())+'\t#'+str(self.state_cnt)
        return name

    def get_holds(self):
        return self.holds

    def get_setups(self):
        return self.setups

    def get_first_table_param(self):
        return round(self.get_clock_rise_time(),5)

    def get_second_table_param(self):
        return round(self.get_signal_rise_time(),5)

    def get_clock_rise_time(self):
        return self.clock_rise_time*self.slew_derate_factor

    def set_clock_rise_time(self,value):
        self.clock_rise_time = value/self.slew_derate_factor

    def get_signal_rise_time(self):
        return self.signal_rise_time*self.slew_derate_factor

    def set_signal_rise_time(self,value):
        self.signal_rise_time = value/self.slew_derate_factor

    def update_lower_th_to_current_delay(self,signal,edge_type):
        self.logger_debug("Setting lower threshold of signal "+signal+" to "+str(self.current_delay[signal][edge_type]))
        self.lower_th[signal][edge_type] = copy(self.current_delay[signal][edge_type])

    def update_upper_th_to_current_delay(self,signal,edge_type):
        self.logger_debug("Setting upper threshold of signal "+signal+" to "+str(self.current_delay[signal][edge_type]))
        self.upper_th[signal][edge_type] = copy(self.current_delay[signal][edge_type])

    def generate_two_edges(self,signal,transition_time,rising_delay,falling_delay,unateness):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')

        if self.state == 'delay':
            start_time   = self.timing_offset - self.clock_period/2.0
            start_time_2 = self.timing_offset + self.clock_period*1.5

            self.append_out('+ 0.0000000e+00 '+str(self.low_value)+'e+00')
            self.add_output_rise_edge(start_time,transition_time)
            self.add_output_fall_edge(start_time_2,transition_time)
            self.append_out(')')

        elif self.state == 'setup':
            start_time   = self.timing_offset
            start_time_2 = self.timing_offset + self.clock_period*2

            if unateness == 'positive_unate':
                start_time   -= rising_delay
                start_time_2 -= falling_delay
            elif unateness == 'negative_unate':
                start_time   -= falling_delay
                start_time_2 -= rising_delay

            first_value = self.low_value
            second_value = self.high_value

            self.append_out('+ 0.0000000e+00 '+str(first_value)+'e+00')
            self.append_out('+ '+str(start_time-transition_time*0.5)+'e-9 '+str(first_value)+'e+00')
            self.append_out('+ '+str(start_time+transition_time*0.5)+'e-09 '+str(second_value)+'e+00')
            self.append_out('+ '+str(start_time_2-transition_time*0.5)+'e-9 '+str(second_value)+'e+00')
            self.append_out('+ '+str(start_time_2+transition_time*0.5)+'e-09 '+str(first_value)+'e+00)')



        elif self.state == 'hold':
            start_time   = self.timing_offset
            start_time_2 = self.timing_offset + self.clock_period*2

            if unateness == 'positive_unate':

                start_time   += rising_delay
                start_time_2 += falling_delay

            elif unateness == 'negative_unate':

                start_time   += falling_delay
                start_time_2 += rising_delay

            mid_time = self.timing_offset + self.clock_period - self.initial_delay
            mid_time_2 = self.timing_offset + self.clock_period + self.initial_delay

            self.append_out('+ 0.0000000e+00 '+str(self.low_value)+'e+00')
            self.add_output_rise_edge(self.timing_offset \
                                      - self.clock_period*0.5,
                                      transition_time)
            self.add_output_fall_edge(start_time, transition_time)

            if mid_time > 0 and mid_time_2 > 0:
                self.add_output_rise_edge(mid_time,transition_time)
                self.add_output_fall_edge(mid_time_2, transition_time)

            self.add_output_rise_edge(start_time_2,transition_time)
            self.append_out(')')


    def set_initial_condition(self,signal):
        if self.probe_signal_directions[signal] == 'positive_unate':
            self.append_out('.IC V('+signal+')='+str(self.low_value))
            self.append_out('.NODESET V('+signal+')='+str(self.low_value))
        elif self.probe_signal_directions[signal] == 'negative_unate':
            self.append_out('.IC V('+signal+')='+str(self.high_value))
            self.append_out('.NODESET V('+signal+')='+str(self.high_value))
        else:
            raise Exception('Probe signal '+signal+' has unknown unate-ness. Please specify \'positive_unate\' or \'negative_unate\'')


    def generate_clock_edge(self,name,direction):
        self.append_out('V'+name+' '+name+' 0 pwl(')
        if direction == 'R':
            #low
            self.append_out('+ 0.0000000e+00 '+str(self.low_value)+'e+00')
            #up
            self.append_out('+ '+str(self.timing_offset - self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset - self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            #down
            self.append_out('+ '+str(self.timing_offset - self.clock_period*0.5 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset - self.clock_period*0.5 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            #up
            self.append_out('+ '+str(self.timing_offset - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            #down
            self.append_out('+ '+str(self.timing_offset + self.clock_period*0.5 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*0.5 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            #up
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            #down
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.5 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.5 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            #up
            self.append_out('+ '+str(self.timing_offset + self.clock_period*2.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*2.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value)+')')
        else:
            #high
            self.append_out('+ 0.0000000e+00 '+str(self.high_value)+'000000e+00')
            self.append_out('+ '+str(self.timing_offset - self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset - self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            #down
            self.append_out('+ '+str(self.timing_offset - self.clock_period*0.5 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset - self.clock_period*0.5 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            #down
            self.append_out('+ '+str(self.timing_offset - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            #up
            self.append_out('+ '+str(self.timing_offset + self.clock_period*0.5 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*0.5 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            #down
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            #up
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.5 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*1.5 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            #down
            self.append_out('+ '+str(self.timing_offset + self.clock_period*2.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_period*2.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value)+')')


    def generate_timing_signals(self):
        import re

        for name,direction in self.clocks.iteritems():
            self.generate_clock_edge(name,direction)
            self.add_probe(name)

        self.logger_debug("Generating "+str(len(self.probe_signals))+" edges.")
        for probe,signal in self.probe_signals.iteritems():
            self.generate_two_edges(signal,
                                    self.signal_rise_time,
                                    self.current_delay[signal][0],
                                    self.current_delay[signal][1],
                                    self.probe_signal_directions[probe])
            #self.logger_debug("Generating edge for "+signal+" with rising delay "+str(self.current_delay[signal][0])+ " and falling delay "+str(self.current_delay[signal][1]))
            self.add_probe(signal)

        #for signal in self.probe_signals.iterkeys():
            self.add_probe(probe)
            self.set_initial_condition(probe)
            self.add_output_cap(probe)

    def add_output_cap(self,out):
        self.append_out('C'+out+' '+out+' 0 ' \
                        +str(self.output_capacitance)+'e-12')

    def get_current_filename(self):
        import os
        name,ext = os.path.splitext(self.output_filename)
        name += '_clk'+str(self.get_clock_rise_time())+'_sig'
        name += str(self.get_signal_rise_time())+'_'+self.state+'_'+str(self.state_cnt)+ext
        return name


    def add_timing_signals(self,clocks,tim_sig):
        import re

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
                    tests.append(re.compile(r"=([\*\d\%\+\/\-]*index[\*\d\%\+\/\-]*)="))

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
                    if self.static_signals.has_key(sig):
                        raise Exception('Timing signal '+sig+' has already been defined as a static signal.')

                self.timing_signals[sig] = {}
                self.current_delay[sig] = [self.initial_delay,self.initial_delay]
                self.current_stepsize[sig] = [self.initial_stepsize,self.initial_stepsize]
                self.direction[sig] = [-1.,-1.]
                self.upper_th[sig] = [self.infinity,self.infinity]
                self.signal_to_clock[sig] = related[0]
                self.probe_signals[related[1]] = sig
                self.probe_signal_directions[related[1]] = related[2]


        self.added_timing_signals = True


    def next_step(self):

        if self.state == 'init':
            self.state = 'delay'
            self.state_cnt = 0
            self.write_spice_file()
            if not self.run() == 0:
                return 1
            if not self.check_timing() == 0:
                return 1

            self.state = 'setup'
            self.state_cnt = 0

        elif self.state == 'setup':
            self.write_spice_file()
            if not self.run() == 0:
                return 1
            if not self.check_timing() == 0:
                return 1

            if self.state_cnt == self.max_setup_steps-1:
                self.state_cnt = 0
                for probe,sig in self.probe_signals.iteritems():
                    # be conservative!
                    # in the case of setup timing this means to take the lower threshold
                    if self.probe_signal_directions[probe] == 'positive_unate':
                        self.setups[sig] = [self.lower_th[sig][0],self.lower_th[sig][1]]
                    elif self.probe_signal_directions[probe] == 'negative_unate':
                        self.setups[sig] = [self.lower_th[sig][1],self.lower_th[sig][0]]

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

                self.state = 'hold'

            else:
                self.state_cnt += 1

        elif self.state == 'hold':
            self.write_spice_file()
            if not self.run() == 0:
                return 1
            if not self.check_timing() == 0:
                return 1

            if self.state_cnt == self.max_hold_steps-1:
                self.state = 'done'
                self.state_cnt = 0
                for probe,sig in self.probe_signals.iteritems():
                    # be conservative!
                    # in the case of hold timing this also means to take the lower threshold,
                    # since for technical reasons it uses the same code as for the setup case, ugly!
                    if self.probe_signal_directions[probe] == 'positive_unate':
                        self.holds[sig] = [self.lower_th[sig][0],self.lower_th[sig][1]]
                    elif self.probe_signal_directions[probe] == 'negative_unate':
                        self.holds[sig] = [self.lower_th[sig][1],self.lower_th[sig][0]]

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


    def check_timing(self):
        # parse result file
        # after this step, all edges are identified
        if not self.parse_print_file() == 0:
            return 1

        # find clock edge
        clock_edges = {}
        for clock_name, clock_dir in self.clocks.iteritems():
            if not clock_edges.has_key(clock_name):
                clock_edges[clock_name] = []
            self.logger_debug('Clock edges for '+clock_name \
                             +': '+str(self.get_rising_edges(clock_name)))
            if (clock_dir == 'R'):
                clock_edges[clock_name] = self.get_rising_edges(clock_name)
                # remove first and middle clock edges, since it is not relevant
                # for the calculations
                del clock_edges[clock_name][0]
                # here, we actually delete entry 2, but since 0 is already
                # dropped
                del clock_edges[clock_name][1]
                self.logger_debug("Rising edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))
            else:
                clock_edges[clock_name] = self.get_falling_edges(clock_name)
                # remove first and middle clock edges, since it is not relevant
                # for the calculations
                del clock_edges[clock_name][0]
                # here, we actually delete entry 2, but since 0 is already
                # dropped
                del clock_edges[clock_name][1]
                self.logger_debug("Falling edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))

        for signal,related in self.probe_signals.iteritems():
            delta_t = [0,0]
            if self.probe_signal_directions[signal] == 'positive_unate':
                r_edges_signal = self.get_rising_edges(signal)
                if r_edges_signal and len(r_edges_signal) > 0:
                    for r_edge in r_edges_signal:
                        delta_t[0] = r_edge
                        self.logger_debug( "Rising edge for "+signal+" at "+str(delta_t[0]))
                        delta_t[0] -= clock_edges[self.signal_to_clock[related]][0]
                        if delta_t[0] < 0 or delta_t[0] > self.clock_period*1.e-9:
                            self.logger_debug("Rising edge for signal "+signal+" too far away from clock edge")
                            delta_t[0] = self.infinity
                        else:
                            self.logger_debug("Rising edge delay is: "+str(delta_t[0]))
                            break
                else:
                    self.logger_debug("Rising edge for signal "+signal+" not found but expected")
                    delta_t[0] = self.infinity

                f_edges_signal = self.get_falling_edges(signal)
                if f_edges_signal and len(f_edges_signal) > 0:
                    for f_edge in f_edges_signal:
                        delta_t[1] = f_edge
                        self.logger_debug( "Falling edge for "+signal+" at "+str(delta_t[1]))
                        delta_t[1] -= clock_edges[self.signal_to_clock[related]][1]
                        if delta_t[1] < 0 or delta_t[1] > self.clock_period*1.e-9:
                            self.logger_debug("Falling edge for signal "+signal+" too far away from clock edge")
                            delta_t[1] = self.infinity
                        else:
                            self.logger_debug("Falling edge delay is: "+str(delta_t[1]))
                            break
                else:
                    self.logger_debug("Falling edge for signal "+signal+" not found but expected")
                    delta_t[1] = self.infinity
            elif self.probe_signal_directions[signal] == 'negative_unate':
                f_edges_signal = self.get_falling_edges(signal)
                if f_edges_signal and len(f_edges_signal) > 0:
                    for f_edge in f_edges_signal:
                        delta_t[1] = f_edge
                        self.logger_debug( "Falling edge for "+signal+" at "+str(delta_t[1]))
                        delta_t[1] -= clock_edges[self.signal_to_clock[related]][0]
                        if delta_t[1] < 0 or delta_t[1] > self.clock_period*1.e-9:
                            self.logger_debug("Falling edge for signal "+signal+" too far away from clock edge")
                            delta_t[1] = self.infinity
                        else:
                            self.logger_debug("Falling edge delay is: "+str(delta_t[1]))
                            break
                else:
                    self.logger_debug("Falling edge for signal "+signal+" not found but expected")
                    delta_t[1] = self.infinity

                r_edges_signal = self.get_rising_edges(signal)
                if r_edges_signal and len(r_edges_signal) > 0:
                    for r_edge in r_edges_signal:
                        delta_t[0] = r_edge
                        self.logger_debug( "Rising edge for "+signal+" at "+str(delta_t[0]))
                        delta_t[0] -= clock_edges[self.signal_to_clock[related]][1]
                        if delta_t[0] < 0 or delta_t[0] > self.clock_period*1.e-9:
                            self.logger_debug("Rising edge for signal "+signal+" too far away from clock edge")
                            delta_t[0] = self.infinity
                        else:
                            self.logger_debug("Rising edge delay is: "+str(delta_t[0]) )
                            break
                else:
                    self.logger_debug("Rising edge for signal "+signal+" not found but expected")
                    delta_t[0] = self.infinity

            if delta_t[0] == self.infinity:
                self.logger_warning('Rising delay for signal '+signal+' could not be determined')
            if delta_t[1] == self.infinity:
                self.logger_warning('Falling delay for signal '+signal+' could not be determined')


            #
            # the following block implements
            # a binary search algorithm that
            # tries to look for the setup and
            # hold time of a signal
            #
            if self.state == 'delay':
                self.delays[related] = delta_t
                self.lower_th[related] = copy(self.current_delay[related])
                self.current_delay[related][0] += self.direction[related][0] * self.current_stepsize[related][0]
                self.current_delay[related][1] += self.direction[related][1] * self.current_stepsize[related][1]
            elif self.state == 'setup' or self.state == 'hold':
                # iterate over rising and falling constraint
                for edge_type in [0,1]:
                    self.logger_debug("Checking delay of "+("rising" if edge_type==0 else 'falling')+" edge of signal "+signal+".")
                    # currently searching in negative direction
                    # (i.e.) signal edge delay getting smaller (or more negative) compared to clock edge
                    if self.direction[related][edge_type] < 0 and delta_t[edge_type] < self.delays[related][edge_type]*self.point_of_failure:
                        self.logger_debug("Delay is fine, keeping neg. direction")
                        self.update_lower_th_to_current_delay(related,edge_type)
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
                        # don't check points twice, step back a bit instead
                        if abs(self.current_delay[related][edge_type] - self.upper_th[related][edge_type]) < self.epsilon:
                            self.logger_debug("Hit upper threshold")
                            self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                            # step half a step back, already went too far
                            self.current_delay[related][edge_type] -= self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

                    elif self.direction[related][edge_type] < 0 and delta_t[edge_type] > self.delays[related][edge_type]*self.point_of_failure:
                        self.logger_debug("Delay of %e is too large"%(delta_t[edge_type]) \
                                         +", switching to pos. direction")
                        self.update_upper_th_to_current_delay(related,edge_type)
                        self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                        self.direction[related][edge_type] = +1.
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

                    # currently searching in positive direction
                    # (i.e.) signal edge delay getting larger compared to clock edge
                    elif self.direction[related][edge_type] > 0 and delta_t[edge_type] < self.delays[related][edge_type]*self.point_of_failure:
                        self.logger_debug("Delay is fine, switching to neg. direction")
                        self.update_lower_th_to_current_delay(related,edge_type)
                        self.direction[related][edge_type] = -1.
                        self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

                    elif self.direction[related][edge_type] > 0 \
                        and delta_t[edge_type] > self.delays[related][edge_type]*self.point_of_failure:
                        debug_string = "Delay of %e is "%(delta_t[edge_type])
                        debug_string += "larger than %e,"%(self.delays[related][edge_type]*self.point_of_failure)
                        debug_string += "keeping pos. direction"
                        self.logger_debug(debug_string)

                        self.update_upper_th_to_current_delay(related,edge_type)
                        self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
                        # don't check points twice, step back a bit instead
                        if abs(self.current_delay[related][edge_type] - self.lower_th[related][edge_type]) < self.epsilon:
                            self.logger_debug("Hit lower threshold")
                            self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
                            # step half a step back, already went too far
                            self.current_delay[related][edge_type] -= self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

                    self.logger_debug("New "+("rising" if edge_type==0 else 'falling')+" edge delay for signal "+related+" is "+str(self.current_delay[related][edge_type]))

            #elif self.state == 'hold':
            #    # iterate over rising and falling constraint
            #    for edge_type in [0,1]:
            #        self.logger_debug("Checking "+("rising" if edge_type==0 else 'falling')+" edge.")
            #        # currently searching in negative direction
            #        # (i.e.) signal edge delay getting smaller (or more negative) compared to clock edge
            #        if self.direction[related][edge_type] < 0 and delta_t[edge_type] < self.delays[related][edge_type]*self.point_of_failure:
            #            self.logger_debug("Delay is fine, keeping direction")
            #            self.logger_debug("Setting upper threshold to "+str(self.current_delay[related][edge_type]))
            #            self.upper_th[related][edge_type] = self.current_delay[related][edge_type]
            #            self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
            #            # don't check points twice, step back a bit instead
            #            if abs(self.current_delay[related][edge_type] - self.upper_th[related][edge_type]) < self.epsilon:
            #                self.logger_debug("Hit upper threshold")
            #                self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
            #                # step half a step back, already went too far
            #                self.current_delay[related][edge_type] -= self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

            #        elif self.direction[related][edge_type] < 0 and delta_t[edge_type] > self.delays[related][edge_type]*self.point_of_failure:
            #            self.logger_debug("Delay is too large, switching direction")
            #            self.logger_debug("Setting lower threshold to "+str(self.current_delay[related][edge_type]))
            #            self.lower_th[related][edge_type] = self.current_delay[related][edge_type]
            #            self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
            #            self.direction[related][edge_type] = +1.
            #            self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

            #        # currently searching in positive direction
            #        # (i.e.) signal edge delay getting larger compared to clock edge
            #        elif self.direction[related][edge_type] > 0 and delta_t[edge_type] < self.delays[related][edge_type]*self.point_of_failure:
            #            self.logger_debug("Delay is fine, switching direction")
            #            self.logger_debug("Setting upper threshold to "+str(self.current_delay[related][edge_type]))
            #            self.upper_th[related][edge_type] = self.current_delay[related][edge_type]
            #            self.direction[related][edge_type] = -1.
            #            self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
            #            self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

            #        elif self.direction[related][edge_type] > 0 and delta_t[edge_type] > self.delays[related][edge_type]*self.point_of_failure:
            #            self.logger_debug("Delay is too large, keeping direction")
            #            self.logger_debug("Setting lower threshold to "+str(self.current_delay[related][edge_type]))
            #            self.lower_th[related][edge_type] = self.current_delay[related][edge_type]
            #            self.current_delay[related][edge_type] += self.direction[related][edge_type] * self.current_stepsize[related][edge_type]
            #            # don't check points twice, step back a bit instead
            #            if abs(self.current_delay[related][edge_type] - self.lower_th[related][edge_type]) < self.epsilon:
            #                self.logger_debug("Hit lower threshold")
            #                self.current_stepsize[related][edge_type] = self.current_stepsize[related][edge_type]/2.
            #                # step half a step back, already went too far
            #                self.current_delay[related][edge_type] -= self.direction[related][edge_type] * self.current_stepsize[related][edge_type]

        return 0

    def parse_print_file(self):
        import subprocess,os
        call = ''
        if self.use_spectre:
            call = ['python', os.environ['BRICK_DIR']+'/source/python/brick_characterizer/parse_print_file_spectre.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold)]
        else:
            call = ['python', os.environ['BRICK_DIR']+'/source/python/brick_characterizer/parse_print_file.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold)]
        self.logger_debug(" ".join(call))
        returncode = subprocess.call(call)#,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

        if not returncode == 0:
            return 1

        import pickle
        with open(self.get_printfile_name()+'_rising') as input:
            self.rising_edges = pickle.load(input)
        with open(self.get_printfile_name()+'_falling') as input:
            self.falling_edges = pickle.load(input)

        #self.logger_debug(str(self.rising_edges))

        return 0


