from brick_characterizer.CharBase import CharBase

class CellRiseFall_Char(CharBase):

    def __init__(self,toplevel,output_filename):
        super(CellRiseFall_Char,self).__init__()

        self.toplevel = toplevel
        self.output_filename = output_filename

        self.input_rise_time = 0.1
        self.load_capacitance = 0.01
        self.clock_rise_time = 0.1 #ns
        self.signal_rise_time = 0.1 #ns
        self.initial_delay = 0.4 #ns

        self.signal_to_clock = {}
        self.source_signals = {}
        self.source_signal_directions = {}

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

    def next_step(self):
        # this class has only one step
        if self.state == 'init':
            self.state = 'delay'

            self.write_spice_file()
            self.run()
            self.check_timing()

            self.state = 'done'

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
                    tests.append(re.compile(r"=(index[\*\d\%\+\/\-]+)="))

                    match = None
                    for test in tests:
                        match = test.search(related[1])
                        while match:
                            cur_probe = test.sub(str(int(eval(match.group(1)))),cur_probe,count=1)
                            match = test.search(cur_probe)

                    self.timing_signals[cur_sig] = {}
                    self.signal_to_clock[cur_sig] = related[0]
                    self.source_signals[cur_probe] = cur_sig
                    self.source_signal_directions[cur_probe] = related[2]
            else:
                if self.added_static_signals:
                    if self.static_signals.has_key(sig):
                        raise Exception('Timing signal '+sig+' has already been defined as a static signal.')

                self.timing_signals[sig] = {}
                self.signal_to_clock[sig] = related[0]
                self.source_signals[related[1]] = sig
                self.source_signal_directions[related[1]] = related[2]


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
                    self.static_signals[cur_sig] = 0
                    if self.added_timing_signals:
                        if self.timing_signals.has_key(cur_sig) or self.clocks.has_key(cur_sig):
                            raise Exception('Static signal '+cur_sig+' has already been defined as a timing or clock signal.')

            else:
                self.static_signals[name] = 0
                if self.added_timing_signals:
                    if self.timing_signals.has_key(name) or self.clocks.has_key(name):
                        raise Exception('Static signal '+name+' has already been defined as a timing or clock signal.')

        self.added_static_signals = True
 

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
 
