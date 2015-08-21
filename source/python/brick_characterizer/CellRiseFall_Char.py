from brick_characterizer.CharBase import CharBase

class CellRiseFall_Char(CharBase):

    def __init__(self,toplevel,output_filename,temperature,use_spectre=False):

        self.toplevel = toplevel
        self.output_filename = output_filename

        self.input_rise_time = 0.1
        self.load_capacitance = 0.01
        self.clock_rise_time = 0.1 #ns
        self.signal_rise_time = 0.1 #ns
        self.initial_delay = 0.4 #ns
        self.simulation_length = 12.0 #ns

        self.slew_lower_rise = 0.3
        self.slew_upper_rise = 0.7
        self.slew_lower_fall = 0.3
        self.slew_upper_fall = 0.7

        self.signal_to_clock = {}
        self.source_signals = {}
        self.probe_signal_directions = {}

        self.delays = {}
        self.transitions = {}

        super(CellRiseFall_Char,self).__init__(temperature,use_spectre)

    def get_delays(self):
        return self.delays

    def get_transitions(self):
        return self.transitions

    def get_first_table_param(self):
        return self.get_input_rise_time()

    def get_second_table_param(self):
        return self.get_load_capacitance()

    def get_input_rise_time(self):
        return self.input_rise_time

    def set_input_rise_time(self,value):
        self.input_rise_time = value

    def get_load_capacitance(self):
        return self.load_capacitance

    def set_load_capacitance(self,value):
        self.load_capacitance = value

    def whats_my_name(self):
        return 'CellRiseFall_Char_inTr'+str(self.input_rise_time)+'_cap'+str(self.load_capacitance)

    def log_my_name(self):
        return self.state+'\tin'+str(self.input_rise_time)+'\tcap'+str(self.load_capacitance)

    def next_step(self):
        # this class has only one step
        if self.state == 'init':
            self.state = 'delay'

            self.write_spice_file()
            if not self.run() == 0:
                return 1
            self.check_timing()

            self.state = 'done'

            return 0

        return 0

    def get_current_filename(self):
        import os
        name,ext = os.path.splitext(self.output_filename)
        return name+'_inTr'+str(self.input_rise_time)+'_cap'+str(self.load_capacitance)+'_'+self.state+ext

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

                    self.signal_to_clock[cur_sig] = related[0]
                    self.source_signals[cur_probe] = cur_sig
                    self.probe_signal_directions[cur_probe] = related[2]
                    self.delays[cur_sig] = []
                    self.transitions[cur_sig] = []
            else:
                if self.added_static_signals:
                    if self.static_signals.has_key(sig):
                        raise Exception('Timing signal '+sig+' has already been defined as a static signal.')

                self.signal_to_clock[sig] = related[0]
                self.source_signals[related[1]] = sig
                self.probe_signal_directions[related[1]] = related[2]
                self.delays[sig] = []
                self.transitions[sig] = []


        self.added_timing_signals = True


    def generate_timing_signals(self):
        import re

        for name,direction in self.clocks.iteritems():
            self.generate_clock_edge(name,direction)
            self.add_probe(name)

        for signal,related in self.source_signals.iteritems():
            self.generate_two_edges(signal,self.signal_rise_time,self.initial_delay,self.initial_delay)
            #self.logger_debug("Generating edge for "+signal+" with rising delay "+str(self.initial_delay)+ " and falling delay "+str(self.initial_delay))

            self.add_probe(related)
            self.add_probe(signal)
            self.add_capacitance(related,self.load_capacitance)


    def generate_clock_edge(self,name,direction):
        self.append_out('V'+name+' '+name+' 0 pwl(')
        if direction == 'R':
            self.append_out('+ 0.0000000e+00 0.0000000e+00')
            self.append_out('+ '+str(self.timing_offset - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*1.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*1.5 + self.clock_rise_time)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*2 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*2 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
        else:
            self.append_out('+ 0.0000000e+00 '+str(self.high_value)+'000000e+00')
            self.append_out('+ '+str(self.timing_offset - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*1.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset*1.5 + self.clock_rise_time)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*2 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset*2 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))


    def generate_two_edges(self,signal,transition_time,rising_delay,falling_delay):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')

        start_time = self.timing_offset - rising_delay
        start_time_2 = self.timing_offset*2 - falling_delay
        first_value = self.low_value
        second_value = self.high_value

        self.append_out('+ 0.0000000e+00 '+str(first_value)+'e+00')
        self.append_out('+ '+str(start_time)+'e-9 '+str(first_value)+'e+0')
        self.append_out('+ '+str(start_time+transition_time)+'e-09 '+str(second_value)+'e+00)')
        self.append_out('+ '+str(start_time_2)+'e-9 '+str(second_value)+'e+00')
        self.append_out('+ '+str(start_time_2+transition_time)+'e-09 '+str(first_value)+'e+00)')

    def add_capacitance(self,signal_name,capacitance):
        self.append_out('C'+signal_name+' '+signal_name+' 0 '+str(capacitance)+'pf')

    def add_pseudo_static_signals(self,signals):
        if not self.added_timing_signals:
            raise Exception('Cannot add pseudo-static signals before timing_signals have been added. Please call this function afterwards.')

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
                    if self.source_signals.has_key(cur_sig) or self.clocks.has_key(cur_sig):
                        pass
                    else:
                        self.static_signals[cur_sig] = 0

            else:
                if self.source_signals.has_key(name) or self.clocks.has_key(name):
                    pass
                else:
                    self.static_signals[name] = 0
        self.added_static_signals = True


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
            if (clock_dir == 'R'):
                cnt = 0
                for edge in self.get_rising_edges(clock_name):
                    if cnt == 1:
                        clock_edges[clock_name].append(edge)
                    cnt = cnt + 1 if cnt < 2 else 0
                self.logger_debug( "Rising edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))
            else:
                cnt = 0
                for edge in self.get_falling_edges(clock_name):
                    if cnt == 1:
                        clock_edges[clock_name].append(edge)
                    cnt = cnt + 1 if cnt < 2 else 0
                self.logger_debug( "Falling edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))



        for source,probe in self.source_signals.iteritems():
            delta_t = [0,0]
            tran = [0,0]
            probe_lc = probe.lower()

            if self.probe_signal_directions[source] == 'positive_unate':
                r_edges_probe = self.get_rising_edges(probe_lc)
                if r_edges_probe and len(r_edges_probe) > 0:
                    # get threshold time for rising transition lower
                    tran[0] = r_edges_probe.pop(0)
                    # get threshold time for switching point
                    delta_t[0] = r_edges_probe.pop(0)
                    delta_t[0] -= clock_edges[self.signal_to_clock[probe]][0]
                    # get threshold time for rising transition upper
                    tran[0] = r_edges_probe.pop(0) - tran[0]
                else:
                    self.logger_debug("Rising edge for signal "+probe_lc+" not found but expected.")

                f_edges_probe = self.get_falling_edges(probe_lc)
                if f_edges_probe and len(f_edges_probe) > 0:
                    # get threshold time for rising transition lower
                    tran[1] = f_edges_probe.pop(0)
                    # get threshold time for switching point
                    delta_t[1] = f_edges_probe.pop(0)
                    delta_t[1] -= clock_edges[self.signal_to_clock[probe]][1]
                    # get threshold time for falling transition upper
                    tran[1] = f_edges_probe.pop(0) - tran[1]
                else:
                    self.logger_debug("Falling edge for signal "+probe_lc+" not found but expected.")


            elif self.probe_signal_directions[source] == 'negative_unate':
                f_edges_probe = self.get_falling_edges(probe_lc)
                if f_edges_probe and len(f_edges_probe) > 0:
                    # get threshold time for falling transition lower
                    tran[1] = f_edges_probe.pop(0)
                    # get threshold time for switching point
                    delta_t[1] = f_edges_probe.pop(0)
                    delta_t[1] -= clock_edges[self.signal_to_clock[probe]][0]
                    # get threshold time for rising transition upper
                    tran[1] = f_edges_probe.pop(0) - tran[1]
                else:
                    self.logger_debug("Falling edge for signal "+probe_lc+" not found but expected.")

                r_edges_probe = self.get_rising_edges(probe_lc)
                if r_edges_probe and len(r_edges_probe) > 0:
                    # get threshold time for rising transition lower
                    tran[0] = r_edges_probe.pop(0)
                    # get threshold time for switching point
                    delta_t[0] = r_edges_probe.pop(0)
                    delta_t[0] -= clock_edges[self.signal_to_clock[probe]][1]
                    # get threshold time for rising transition upper
                    tran[0] = r_edges_probe.pop(0) - tran[0]
                else:
                    self.logger_debug("Rising edge for signal "+probe_lc+" not found but expected.")

            self.delays[probe] = delta_t
            self.transitions[probe] = tran

            self.logger_debug('Delays for signal \''+probe+'\' are rising: '+str(self.delays[probe][0])+' and falling: '+str(self.delays[probe][1]))
            self.logger_debug('Transition times for signal \''+probe+'\' are rising: '+str(self.transitions[probe][0])+' and falling: '+str(self.transitions[probe][1]))

        return 0

    def parse_print_file(self):
        import subprocess,os
        call = ''
        if self.use_spectre:
            call = ['python', os.environ['BRICK_DIR']+'/source/python/brick_characterizer/parse_print_file_spectre.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold), str(self.high_value*self.slew_lower_rise), str(self.high_value*self.slew_upper_rise), str(self.high_value*self.slew_lower_fall), str(self.high_value*self.slew_upper_fall)]
        else:
            call = ['python', os.environ['BRICK_DIR']+'/source/python/brick_characterizer/parse_print_file.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold), str(self.high_value*self.slew_lower_rise), str(self.high_value*self.slew_upper_rise), str(self.high_value*self.slew_lower_fall), str(self.high_value*self.slew_upper_fall)]

        self.logger_debug(" ".join(call))
        returncode = subprocess.call(call)

        if not returncode == 0:
            return 1

        import pickle
        with open(self.get_printfile_name()+'_rising') as input:
            self.rising_edges = pickle.load(input)
        with open(self.get_printfile_name()+'_falling') as input:
            self.falling_edges = pickle.load(input)

        return 0
