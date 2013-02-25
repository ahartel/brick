import re

class LibBackend:

    def __init__(self,constr_templ):
        self.indentation = 0
        self.buses = {}
        self.constraint_template = constr_templ

        self.bus_reg = re.compile(r"([\w_]+)\[(\d+):(\d+)\]")

    def write_templates(self):
        dim1 = len(self.constraint_template[0])
        dim2 = len(self.constraint_template[1])
        self.constraint_template_name = 'constraint_template'+str(dim1)+'x'+str(dim2)
        output = ['lu_table_template (constraint_template'+str(dim1)+'x'+str(dim2)+') {']
        output += ['\tvariable_1 : related_pin_transition;']
        output += ['\tvariable_2 : constrained_pin_transition;']
        output += ['\tindex_1 ("'+', '.join([str(x) for x in self.constraint_template[0]])+'");']
        output += ['\tindex_2 ("'+', '.join([str(x) for x in self.constraint_template[1]])+'");']

        output += ['}']
        return output

    def write_bus_def(self,from_bit,to_bit,downto):
        width = abs(from_bit-to_bit)+1

        if not self.buses.has_key('bus'+str(width)):
            output = ['type (bus'+str(width)+') {']
            output += ['\tbase_type : array;']
            output += ['\tdata_type : bit;']
            output += ['\tbit_width : '+str(width)+';']
            output += ['\tbit_from : '+str(from_bit)+';']
            output += ['\tbit_to : '+str(to_bit)+';']
            output.append('}')

            self.buses['bus'+str(width)] = [from_bit,to_bit,downto]

            return output
        else:
            return []

    def indent(self,input_list,num=None):
        output_list = []
        for line in input_list:
            if num:
                output_list.append(''.join(['\t' for i in range(num)])+line)
            else:
                output_list.append(''.join(['\t' for i in range(self.indentation)])+line)

        return output_list

    def transform_timing_signals(self,timing_signals):
        new_signals = {}
        for bus in timing_signals:
            m = self.bus_reg.search(bus)
            if m:
                smaller = int(m.group(3))
                larger = int(m.group(2))
                if smaller >= larger:
                    smaller,larger = larger,smaller

                for i in range(smaller,larger+1):
                    signal_name = m.group(1)+'['+str(i)+']'
                    new_signals[signal_name] = timing_signals[bus][0]
            else:
                new_signals[bus] = timing_signals[bus][0]

        return new_signals


    def write_setup_timing(self,timing_signals,setups,signal):
        output = []
        if setups.has_key(signal):
            output += self.indent(['timing() {'])
            self.indentation += 1
            try:
                output += self.indent(['related_pin : "'+timing_signals[signal]+'";'])
            except KeyError:
                print "Error in Library generation. Pin "+signal+" is not in timing_signals list. Unable to determine related_pin. Please change this and re-run. Omitting timing block for setup_cosntraint for this pin."
                return []
            output += self.indent(['timing_type : "setup_rising";'])

            # rising table
            output += self.indent(['rise_constraint ('+self.constraint_template_name+') {'])
            self.indentation += 1
            output+= self.indent(['index_1 ("'+', '.join([str(x) for x in self.constraint_template[0]])+'");'])
            output+= self.indent(['index_2 ("'+', '.join([str(x) for x in self.constraint_template[1]])+'");'])
            values = ['values (']
            for i in range(len(self.constraint_template[0])):
                values[i] += '"'
                values[i] += ', '.join([str(setups[signal][self.constraint_template[0][i]][self.constraint_template[1][j]][0]) for j in range(len(self.constraint_template[1]))])
                if i == len(self.constraint_template[0])-1:
                    values[i] += '"'
                else:
                    values[i] += '", \\'
                    values.append('')
            values [len(self.constraint_template[0])-1] += ');'
            output += self.indent(values)
            self.indentation -= 1
            output += self.indent(['}'])
            # fallng table
            output += self.indent(['fall_constraint ('+self.constraint_template_name+') {'])
            self.indentation += 1
            output+= self.indent(['index_1 ("'+', '.join([str(x) for x in self.constraint_template[0]])+'");'])
            output+= self.indent(['index_2 ("'+', '.join([str(x) for x in self.constraint_template[1]])+'");'])
            values = ['values (']
            for i in range(len(self.constraint_template[0])):
                values[i] += '"'
                values[i] += ', '.join([str(setups[signal][self.constraint_template[0][i]][self.constraint_template[1][j]][1]) for j in range(len(self.constraint_template[1]))])
                if i == len(self.constraint_template[0])-1:
                    values[i] += '"'
                else:
                    values[i] += '", \\'
                    values.append('')
            values [len(self.constraint_template[0])-1] += ');'
            output += self.indent(values)

            self.indentation -= 1
            output += self.indent(['}'])
            self.indentation -= 1
            output += self.indent(['}'])

        return output

    def write_hold_timing(self,timing_signals,holds,signal):
        output = []
        if holds.has_key(signal):
            output += self.indent(['timing() {'])
            self.indentation += 1
            try:
                output += self.indent(['related_pin : "'+timing_signals[signal]+'";'])
            except KeyError:
                print "Error in Library generation. Pin "+signal+" is not in timing_signals list. Unable to determine related_pin. Please change this and re-run. Omitting timing block for setup_cosntraint for this pin."
                return []
            output += self.indent(['timing_type : "hold_rising";'])

            # rising table
            output += self.indent(['rise_constraint ('+self.constraint_template_name+') {'])
            self.indentation += 1
            output+= self.indent(['index_1 ("'+', '.join([str(x) for x in self.constraint_template[0]])+'");'])
            output+= self.indent(['index_2 ("'+', '.join([str(x) for x in self.constraint_template[1]])+'");'])
            values = ['values (']
            for i in range(len(self.constraint_template[0])):
                values[i] += '"'
                values[i] += ', '.join([str(holds[signal][self.constraint_template[0][i]][self.constraint_template[1][j]][0]) for j in range(len(self.constraint_template[1]))])
                if i == len(self.constraint_template[0])-1:
                    values[i] += '"'
                else:
                    values[i] += '", \\'
                    values.append('')
            values [len(self.constraint_template[0])-1] += ');'
            output += self.indent(values)
            self.indentation -= 1
            output += self.indent(['}'])
            # fallng table
            output += self.indent(['fall_constraint ('+self.constraint_template_name+') {'])
            self.indentation += 1
            output+= self.indent(['index_1 ("'+', '.join([str(x) for x in self.constraint_template[0]])+'");'])
            output+= self.indent(['index_2 ("'+', '.join([str(x) for x in self.constraint_template[1]])+'");'])
            values = ['values (']
            for i in range(len(self.constraint_template[0])):
                values[i] += '"'
                values[i] += ', '.join([str(holds[signal][self.constraint_template[0][i]][self.constraint_template[1][j]][1]) for j in range(len(self.constraint_template[1]))])
                if i == len(self.constraint_template[0])-1:
                    values[i] += '"'
                else:
                    values[i] += '", \\'
                    values.append('')
            values [len(self.constraint_template[0])-1] += ');'
            output += self.indent(values)

            self.indentation -= 1
            output += self.indent(['}'])
            self.indentation -= 1
            output += self.indent(['}'])



        return output

    def iterate_power_signals(self,pin_list):
        output = []
        # write bus and pin definitions
        for signal,voltage in pin_list.iteritems():
            #
            # pg_pins
            #
            output += self.indent(['pg_pin ('+signal+') {'])
            self.indentation +=1
            pwr_cnt = 0
            gnd_cnt = 0
            # here
            if voltage > 0:
                output += self.indent(['pg_type : primary_power;'])
                output += self.indent(['voltage_name : COREVDD'+str(pwr_cnt)+';'])
                pwr_cnt += 1
            else:
                output += self.indent(['pg_type : primary_ground;'])
                output += self.indent(['voltage_name : COREGND'+str(gnd_cnt)+';'])
                gnd_cnt += 1

            # end of pin block
            self.indentation -= 1
            output += self.indent(['}'])

        return output

    def create_power_names(self,powers):
        output = []
        pwr_cnt = 0
        gnd_cnt = 0
        for voltage in powers.itervalues():
            if voltage > 0:
                output += ['voltage_map(COREVDD'+str(pwr_cnt)+', '+str(voltage)+');']
            else:
                output += ['voltage_map(COREGND'+str(gnd_cnt)+', '+str(voltage)+');']
        return output

    def iterate_output_signals(self,pin_list):
        output = []
        # write bus and pin definitions
        for signal in pin_list:
            m = self.bus_reg.search(signal)
            if m:
                #
                # buses
                #
                smaller = int(m.group(3))
                larger = int(m.group(2))
                if smaller >= larger:
                    smaller,larger = larger,smaller

                width = abs(smaller-larger)+1

                output += self.indent(['bus ('+m.group(1)+') {'])
                self.indentation +=1
                output += self.indent(['bus_type : bus'+str(width)+';'])
                output += self.indent(['direction : output;'])

                for i in range(smaller,larger+1):
                    signal_name = m.group(1)+'['+str(i)+']'
                    output += self.indent(['pin ('+signal_name+') {'])
                    self.indentation +=1
                    # here
                    output += self.indent(['max_capacitance : 0.010;'])

                    if m.group(1) == 'd_out_pst' or m.group(1) == 'd_out_pre':
                        output += self.indent(['timing() {'])
                        self.indentation += 1

                        if m.group(1) == 'd_out_pst':
                            output += self.indent(['related_pin : "clk_pst";'])
                        elif m.group(1) == 'd_out_pre':
                            output += self.indent(['related_pin : "clk_pre";'])

                        output += self.indent(['cell_rise(scalar) {',
                            '\tvalues( " 0.200 ");',
                            '}'])
                        output += self.indent(['cell_fall(scalar) {',
                            '\tvalues( " 0.200 ");',
                            '}'])
                        output += self.indent(['rise_transition(scalar) {',
                            '    values( " 0.100 ");',
                            '}',
                            'fall_transition(scalar) {',
                            '    values( " 0.100 ");',
                            '}'])

                        # end of timing block
                        self.indentation -= 1
                        output += self.indent(['}'])
                    # end of pin block
                    self.indentation -= 1
                    output += self.indent(['}'])

                self.indentation -= 1
                output += self.indent(['}'])
            else:
                #
                # pins
                #
                output += self.indent(['pin ('+signal+') {'])
                self.indentation +=1
                output += self.indent(['direction : output;'])
                # here
                output += self.indent(['max_capacitance : 0.010;'])


                # end of pin block
                self.indentation -= 1
                output += self.indent(['}'])

        return output


    def iterate_input_signals(self,pin_list,caps,timing_signals,setups,holds):
        output = []
        # write bus and pin definitions
        for signal in pin_list:
            m = self.bus_reg.search(signal)
            if m:
                #
                # buses
                #
                smaller = int(m.group(3))
                larger = int(m.group(2))
                if smaller >= larger:
                    smaller,larger = larger,smaller

                width = abs(smaller-larger)+1

                output += self.indent(['bus ('+m.group(1)+') {'])
                self.indentation +=1
                output += self.indent(['bus_type : bus'+str(width)+';'])
                output += self.indent(['direction : input;'])

                for i in range(smaller,larger+1):
                    signal_name = m.group(1)+'['+str(i)+']'
                    output += self.indent(['pin ('+signal_name+') {'])
                    self.indentation +=1
                    # here
                    output += self.indent(['capacitance : '+str(caps[signal_name]/1.e-12)+';'])

                    output += self.write_setup_timing(timing_signals,setups,signal_name)
                    output += self.write_hold_timing(timing_signals,holds,signal_name)

                    self.indentation -= 1
                    output += self.indent(['}'])

                self.indentation -= 1
                output += self.indent(['}'])
            else:
                #
                # pins
                #
                output += self.indent(['pin ('+signal+') {'])
                self.indentation +=1
                output += self.indent(['direction : input;'])
                output += self.indent(['capacitance : '+str(caps[signal_name]/1.e-12)+';'])

                output += self.write_setup_timing(timing_signals,setups,signal)
                output += self.write_hold_timing(timing_signals,holds,signal)

                self.indentation -= 1
                output += self.indent(['}'])

        return output

    def write(self,library,cell,filename,inputs,outputs,powers,caps,timing_signals,setups,holds):
        output = []

        timing_signals = self.transform_timing_signals(timing_signals)


        output += ['library ('+library+') {']
        self.indentation = 1

        output += self.indent(['delay_model : table_lookup;',
        'capacitive_load_unit (1,pf) ;',
        'voltage_unit : "1V" ;',
        'current_unit : "1mA" ;',
        'time_unit : "1ns" ;',
        'pulling_resistance_unit : "1kohm";',
        'operating_conditions("NCCOM"){',
        '\tprocess : 1; /* TT TT_25 */',
        '\ttemperature : 25;',
        '\tvoltage : 1.2;',
        '\ttree_type : "balanced_tree";',
        '}',
        'default_operating_conditions : NCCOM ;',
        ])

        output += self.indent(self.create_power_names(powers))

        output += self.indent(self.write_templates())

        # write bus defs
        for bus in inputs:
            m = self.bus_reg.search(bus)
            if m:
                left = int(m.group(3))
                right = int(m.group(2))
                downto = True
                if left <= right:
                    downto = False

                output.extend(self.indent(self.write_bus_def(left,right,downto)))

        output += self.indent(['cell ('+cell+') {'])
        self.indentation += 1

        output += self.iterate_input_signals(inputs,caps,timing_signals,setups,holds)
        output += self.iterate_output_signals(outputs)
        output += self.iterate_power_signals(powers)

        self.indentation -= 1
        output += self.indent(['}']) # end of cell
        self.indentation -= 1
        output += ['}'] # end of library
        self.indentation -= 1

        f = open(filename,'w')
        for line in output:
            f.write(line+"\n")
        f.close()

