class SimulationRun:
    def __init__(self,toplevel):
        self.toplevel = toplevel
        self.spice_output = []
        self.include_netlists = []
        self.static_signals = {}
        self.timing_signals = {}
        self.probe_signals = {}
        self.vdd = 1.2
        self.gnd = 0.0
        self.output_dir = 'output'
        self.timing_offset = 5.0 #ns
        self.simulation_length = 10.0 #ns
        self.rising_edges = {}
        self.falling_edges = {}
        self.rise_threshold = 0.5
        self.fall_threshold = 0.5

    def set_rise_threshold(self,value):
        if value > 1:
            raise Exception('rise threshold cannot be greater than 1')

        self.rise_threshold = value

    def set_fall_threshold(self,value):
        if value > 1:
            raise Exception('fall threshold cannot be greater than 1')
        self.fall_threshold = value

    def set_vdd(self,value):
        self.vdd = 1.2

    def set_gnd(self,value):
        self.gnd = 0.0

    def append_out(self,line):
        self.spice_output.append(line)

    def add_static_signals(self,signals):
        self.static_signals = signals

    def generate_single_signal(self,signal,value):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')
        if value == 1:
            value = str(self.vdd)
        else:
            value = str(self.gnd)

        self.append_out('+ 0.0000000e+00 '+value+'000000e+00')
        self.append_out('+ 2.4999999e-13 '+value+'000000e+00')
        self.append_out('+ 5.0000000e-09 '+value+'000000e+00)')

    def generate_single_edge(self,signal,rise_time,start_time,edge_type):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')
        if edge_type == 'R':
            self.append_out('+ 0.0000000e+00 0.0000000e+00')
            self.append_out('+ '+str(start_time)+'e-9 0.0000000e+00')
            self.append_out('+ '+str(start_time+rise_time)+'000000e-09 '+str(self.vdd)+'000000e+00)')
        else:
            self.append_out('+ 0.0000000e+00 '+str(self.vdd)+'000000e+00')
            self.append_out('+ '+str(start_time)+'e-9 '+str(self.vdd)+'000000e+00')
            self.append_out('+ '+str(start_time+rise_time)+'000000e-09 '+str(self.gnd)+'000000e+00)')

    def generate_static_signals(self):
        import re
        self.append_out('Vvdd vdd 0 '+str(self.vdd))
        self.append_out('Vgnd gnd 0 '+str(self.gnd))

        for (signal,value) in self.static_signals.iteritems():
            # check for buses
            m = re.match(r"(.+?)\[(\d+):(\d+)\]",signal)
            if m:
                #bus
                smaller = 0
                larger = 0
                if m.group(2) >= m.group(3):
                    smaller = int(m.group(3))
                    larger = int(m.group(2))
                else:
                    smaller = int(m.group(2))
                    larger = int(m.group(3))

                for i in range(smaller,larger+1):
                    self.generate_single_signal(m.group(1)+'['+str(i)+']',value)

            else:
                #single net
                self.generate_single_signal(signal,value)

    def add_probe(self,signal):
        self.append_out('.print v('+signal+')')
        self.append_out('.probe v('+signal+')')


    def generate_timing_signals(self):
        import re

        self.generate_single_edge(self.clock[0],0.1,self.timing_offset,self.clock[1])
        self.add_probe(self.clock[0])

        for (signal,value) in self.timing_signals.iteritems():
            # check for buses
            m = re.match(r"(.+?)\[(\d+):(\d+)\]",signal)
            if m:
                #bus
                smaller = 0
                larger = 0
                if m.group(2) >= m.group(3):
                    smaller = int(m.group(3))
                    larger = int(m.group(2))
                else:
                    smaller = int(m.group(2))
                    larger = int(m.group(3))

                for i in range(smaller,larger+1):
                    self.generate_single_edge(m.group(1)+'['+str(i)+']',0.1,self.timing_offset,value)
                    self.add_probe(m.group(1)+'['+str(i)+']')
            else:
                #single net
                self.generate_single_edge(signal,0.1,self.timing_offset,value)
                self.add_probe(signal)

        for signal in self.probe_signals.iterkeys():
            self.add_probe(signal)

    def write_spice_file(self,filename):
        self.output_filename = filename

        self.append_out('* brick characterizer')
        self.write_include_netlists()
        self.write_header()
        self.generate_static_signals()
        self.generate_timing_signals()

        f = open(filename,'w')
        for line in self.spice_output:
            f.write(line+'\n')
        #f.write('.subckt test\n')
        #f.write('.ends')
        f.close()

    def add_include_netlist(self,netlist):
        import os
        if not os.path.isfile(netlist):
            raise Exception('include-netlist not found')

        self.include_netlists.append(netlist)

    def add_timing_signals(self,clock,tim_sig,probe_sig,probe_sig_dir):
        self.clock = clock
        self.timing_signals = tim_sig
        self.probe_signals = probe_sig
        self.probe_signal_directions = probe_sig_dir

    def write_header(self):
        self.append_out('.param tran_tend='+str(self.simulation_length)+'000000e-09')
        self.append_out('.tran 1.00e-12 \'tran_tend\'')
        self.append_out('')

    def write_include_netlists(self):
        for netlist in self.include_netlists:
            self.append_out('.include '+netlist+'')
        self.append_out('')

    def run(self):
        import subprocess
        call = ['ultrasim', '-f', self.output_filename, '-raw', self.output_dir, '-format', 'sst2', '-top', self.toplevel]
        self.process = subprocess.Popen(call,stdout=subprocess.PIPE)
        self.process.wait()

    def oom(self,exp):
        if exp == 'm':
            return 1.e-3
        elif exp == 'u':
            return 1.e-6
        elif exp == 'n':
            return 1.e-9
        elif exp == 'p':
            return 1.e-12

    def check_timing(self):
        self.parse_print_file()

        clock_edge = None
        if (self.clock[1] == 'R'):
            clock_edge = self.rising_edges[self.clock[0]]
            print "Rising edge of "+self.clock[0]+" at "+str(clock_edge)
        else:
            clock_edge = self.falling_edges[self.clock[0]]
            print "Falling edge of "+self.clock[0]+" at "+str(clock_edge)

        for signal,related in self.probe_signals.iteritems():
            delta_t = 0
            signal_lc = signal.lower()
            if self.probe_signal_directions[signal] == 'R':
                if self.rising_edges.has_key(signal_lc):
                    delta_t = self.rising_edges[signal_lc]
                    print "Rising edge for "+signal+" at "+str(delta_t)
                    delta_t -= clock_edge
                    print "Delay: "+str(delta_t)
                else:
                    raise Exception("Rising edfe for signal "+signal+" not found but expected")
            elif self.probe_signal_directions[signal] == 'F':
                if self.falling_edges.has_key(signal_lc):
                    delta_t = self.falling_edges[signal_lc]
                    print "Falling edge for "+signal+" at "+str(delta_t)
                    delta_t -= clock_edge
                    print "Delay: "+str(delta_t)
                else:
                    raise Exception("Falling edfe for signal "+signal+" not found but expected")



    def parse_print_file(self):
        import os,re
        f = open(self.output_dir+'/'+os.path.splitext(self.output_filename)[0]+'.print0')
        comment = re.compile(r"^\*")
        start_value = re.compile(r"^x")
        stop_value = re.compile(r"^y")
        signal_name = re.compile(r"(\w+)")
        numbers = re.compile(r"([\d\.]+)([munp]?)\s+([\d\.]+)([munp]?)")
        found_start = 0
        current_signal_name = ''
        signal_value = 0

        for line in f:
            if found_start > 0:
                if found_start < 3:
                    found_start += 1
                    continue
                elif found_start == 3:
                    found_start += 1
                    m = signal_name.search(line)
                    if m:
                        current_signal_name = m.group(1)
                        signal_value = 0
                else:
                    pass
                    if stop_value.match(line):
                        found_start = 0
                    else:
                        m = numbers.search(line)
                        if m:
                            time = float(m.group(1))
                            if m.group(2):
                                time = time*self.oom(m.group(2))
                            voltage = float(m.group(3))
                            if m.group(4):
                                voltage = voltage*self.oom(m.group(4))
                            if signal_value == 0:
                                if voltage < self.vdd*self.rise_threshold:
                                    signal_value = 'R'
                                elif voltage > self.vdd*self.fall_threshold:
                                    signal_value = 'F'
                            elif signal_value == 'R':
                                if voltage > self.vdd*self.rise_threshold:
                                    self.rising_edges[current_signal_name] = time
                                    signal_value = 1
                            elif signal_value == 'F':
                                if voltage < self.vdd*self.fall_threshold:
                                    self.falling_edges[current_signal_name] = time
                                    signal_value = 1
            else:
                if comment.match(line):
                    continue
                elif start_value.match(line):
                    found_start = 1

        f.close()


