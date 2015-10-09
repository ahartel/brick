def oom(exp):
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
    elif exp == 'a':
        return 1.e-18
    elif exp == 'z':
        return 1.e-21
    elif exp == 'y':
        return 1.e-24
    elif exp == 'k':
        return 1.e3
    elif exp == 'M':
        return 1.e6
    elif exp == 'G':
        return 1.e9
    elif exp == 'T':
        return 1.e12


def parse_print_file(filename,rise_th,fall_th):
    import re
    f = open(filename)
    comment = re.compile(r"^\*")
    start_value = re.compile(r"^x")
    stop_value = re.compile(r"^y")
    signal_name = re.compile(r"time\s*([\w\[\]\(\)\.]+)\s*$")
    #signal_name_wrap = re.compile(r"\s+\+\s+\+\s+([\w\[\]\(\)]+)")
    numbers = re.compile(r"([\d\.]+)\s([TGMkmunpfazy]?)\s+([\d\.]+)\s([TGMkmunpfazy]?)")
    found_start = 0
    current_signal_name = ''
    signal_value = 0
    read_numbers = False
    rising_edges = {}
    falling_edges = {}

    rise_check_time = 10.0e-9
    fall_check_time = 10.0e-9
    check_wait_time = 0.7e-9
    epsilon = 0.01
    last_voltage = 0

    for line in f:
        if found_start > 0:
            if found_start == 1 and not read_numbers:
                m = signal_name.search(line)
                if m:
                    current_signal_name = m.group(1)
                    signal_value = 0
                    read_numbers = True
                    # print "Found signal name "+current_signal_name
                else:
                    pass
                    # print "No signal name found"
                    # print line
                    #m = signal_name_wrap.match(line)
                    #if m:
                    #    current_signal_name += m.group(1)
                    #else:
                    #    read_numbers = True

                found_start += 1
                #return
        else:
            read_numbers = False
            if comment.match(line):
                continue
            elif start_value.match(line):
                # print "Found start"
                found_start = 1

        if read_numbers:
            if stop_value.match(line):
                found_start = 0
            else:
                m = numbers.search(line)
                if m:
                    time = float(m.group(1))
                    if m.group(2):
                        time = time*oom(m.group(2))
                    voltage = float(m.group(3))
                    if m.group(4):
                        voltage = voltage*oom(m.group(4))
                    if signal_value == 0:
                        if voltage < fall_th:
                            signal_value = 'R'
                        elif voltage > rise_th:
                            signal_value = 'F'
                    elif signal_value == 'R':
                        if voltage > rise_th:
                            # found a threshold crossing
                            # register a rising edge and go
                            # to check state
                            if not rising_edges.has_key(current_signal_name):
                                rising_edges[current_signal_name] = []
                            rising_edges[current_signal_name].append(time)
                            # go to check state
                            signal_value = 'R_check'
                            rise_check_time = time
                            last_voltage = voltage
                    elif signal_value == 'R_check':
                        # if max. check state time has been reached
                        # check again if the signal has settled high
                        if time > (rise_check_time + check_wait_time):
                            if voltage < rise_th:
                                # drop last rising edge if signal hasn't
                                # settled high
                                del rising_edges[current_signal_name][-1]
                                #print "Dropping rising edge for "+current_signal_name
                                # since last rising edge was a failure, look again for a rising edge
                                signal_value = 'R'
                            else:
                                # go look for a falling edge
                                signal_value = 'F'
                        # if max. check state time has not been reached
                        # check for monotony
                        else:
                            if last_voltage > voltage and (last_voltage - voltage) > epsilon:
                                del rising_edges[current_signal_name][-1]
                                #print "Dropping rising edge for "+current_signal_name
                                signal_value = 'R_wait'
                            else:
                                last_voltage = voltage

                    elif signal_value == 'R_wait':
                        if time > (rise_check_time + check_wait_time):
                            if voltage < fall_th:
                                signal_value = 'R'
                            elif voltage > rise_th:
                                signal_value = 'F'

                    elif signal_value == 'F':
                        if voltage < fall_th:
                            # found a threshold crossing
                            # register a falling edge and go
                            # to check state
                            if not falling_edges.has_key(current_signal_name):
                                falling_edges[current_signal_name] = []
                            falling_edges[current_signal_name].append(time)
                            # go to check state
                            signal_value = 'F_check'
                            fall_check_time = time
                            last_voltage = voltage

                    elif signal_value == 'F_check':
                        # if max. check state time has been reached
                        # check again if the signal has settled low
                        if time > (fall_check_time + check_wait_time):
                            if voltage > fall_th:
                                del falling_edges[current_signal_name][-1]
                                #print "Dropping falling edge for "+current_signal_name
                                # since last falling edge was a failure, look again for a falling edge
                                signal_value = 'F'
                            else:
                                signal_value = 'R'
                        # if max. check state time has not been reached
                        # check for monotony
                        else:
                            if last_voltage < voltage and (voltage - last_voltage) > epsilon:
                                del falling_edges[current_signal_name][-1]
                                #print "Dropping falling edge for "+current_signal_name
                                signal_value = 'F_wait'
                            else:
                                last_voltage = voltage

                    elif signal_value == 'F_wait':
                        if time > (fall_check_time + check_wait_time):
                            if voltage < fall_th:
                                signal_value = 'F'
                            elif voltage > rise_th:
                                signal_value = 'R'

    f.close()

    # print rising_edges
    # print falling_edges

    return rising_edges,falling_edges


def parse_print_file_tran(filename,rise_th,fall_th,slew_lower_rise,slew_upper_rise,slew_lower_fall,slew_upper_fall):
    import re
    f = open(filename)
    comment = re.compile(r"^\*")
    start_value = re.compile(r"^x")
    stop_value = re.compile(r"^y")
    signal_name = re.compile(r"time\s*([\w\[\]\(\)\.]+)\s*$")
    #signal_name_wrap = re.compile(r"\s+\+\s+\+\s+([\w\[\]\(\)]+)")
    numbers = re.compile(r"([\d\.]+)\s([TGMkmunpfazy]?)\s+([\d\.]+)\s([TGMkmunpfazy]?)")
    found_start = 0
    current_signal_name = ''
    signal_value = 0
    read_numbers = False
    rising_edges = {}
    falling_edges = {}

    for line in f:
        if found_start > 0:
            if found_start == 1 and not read_numbers:
                m = signal_name.search(line)
                if m:
                    current_signal_name = m.group(1)
                    signal_value = 0
                    read_numbers = True
                    # print "Found signal name "+current_signal_name
                else:
                    pass
                    # print "No signal name found"
                    # print line
                    #m = signal_name_wrap.match(line)
                    #if m:
                    #    current_signal_name += m.group(1)
                    #else:
                    #    read_numbers = True

                found_start += 1
                #return
        else:
            read_numbers = False
            if comment.match(line):
                continue
            elif start_value.match(line):
                # print "Found start"
                found_start = 1

        if read_numbers:
            if stop_value.match(line):
                found_start = 0
            else:
                m = numbers.search(line)
                if m:
                    time = float(m.group(1))
                    if m.group(2):
                        time = time*oom(m.group(2))
                    voltage = float(m.group(3))
                    if m.group(4):
                        voltage = voltage*oom(m.group(4))
                    if signal_value == 0:
                        if not rising_edges.has_key(current_signal_name):
                            rising_edges[current_signal_name] = []
                        if not falling_edges.has_key(current_signal_name):
                            falling_edges[current_signal_name] = []

                        if voltage < fall_th:
                            signal_value = 'R'
                        elif voltage > rise_th:
                            signal_value = 'F'
                    elif signal_value == 'R':
                        if voltage > slew_lower_rise:
                            rising_edges[current_signal_name].append(time)
                            signal_value = 'R1'
                    elif signal_value == 'R1':
                        if voltage > rise_th:
                            rising_edges[current_signal_name].append(time)
                            signal_value = 'R2'
                    elif signal_value == 'R2':
                        if voltage > slew_upper_rise:
                            rising_edges[current_signal_name].append(time)
                            signal_value = 'F'

                    elif signal_value == 'F':
                        if voltage < slew_upper_fall:
                            falling_edges[current_signal_name].append(time)
                            signal_value = 'F1'
                    elif signal_value == 'F1':
                        if voltage < fall_th:
                            falling_edges[current_signal_name].append(time)
                            signal_value = 'F2'
                    elif signal_value == 'F2':
                        if voltage < slew_lower_fall:
                            falling_edges[current_signal_name].append(time)
                            signal_value = 'R'

    f.close()
    return rising_edges,falling_edges


if __name__ == '__main__':
    import getopt,sys
    opts, args = getopt.getopt(sys.argv[1:],"")
    filename = args[0]
    rise_th = args[1]
    fall_th = args[2]

    rising_edges = None
    falling_edges = None

    if len(args) > 3:
        slew_lower_rise = args[3]
        slew_upper_rise = args[4]
        slew_lower_fall = args[5]
        slew_upper_fall = args[6]
        rising_edges,falling_edges = parse_print_file_tran(filename,float(rise_th),float(fall_th),float(slew_lower_rise),float(slew_upper_rise),float(slew_lower_fall),float(slew_upper_fall))
    else:
        rising_edges,falling_edges = parse_print_file(filename,float(rise_th),float(fall_th))

    import pickle
    with open(filename+'_rising', 'w') as output:
        pickle.dump(rising_edges,output,pickle.HIGHEST_PROTOCOL)
    with open(filename+'_falling', 'w') as output:
        pickle.dump(falling_edges,output,pickle.HIGHEST_PROTOCOL)

