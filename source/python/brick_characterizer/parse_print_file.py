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
    elif exp == 'k':
        return 1.e3
    elif exp == 'M':
        return 1.e6
    elif exp == 'G':
        return 1.e9


def parse_print_file(filename,rise_th,fall_th):
    import re
    f = open(filename)
    comment = re.compile(r"^\*")
    start_value = re.compile(r"^x")
    stop_value = re.compile(r"^y")
    signal_name = re.compile(r"\s+([\w\[\]]+)\s+$")
    signal_name_wrap = re.compile(r"\s+\+\s+\+\s+([\w\[\]]+)")
    numbers = re.compile(r"([\d\.]+)([GMkmunpf]?)\s+([\d\.]+)([GMkmunpf]?)")
    found_start = 0
    current_signal_name = ''
    signal_value = 0
    read_numbers = False
    rising_edges = {}
    falling_edges = {}

    for line in f:
        if found_start > 0:
            if found_start < 3:
                found_start += 1
                continue
            elif found_start >= 3 and not read_numbers:
                m = signal_name.match(line)
                if m:
                    current_signal_name = m.group(1)
                    signal_value = 0
                else:
                    m = signal_name_wrap.match(line)
                    if m:
                        current_signal_name += m.group(1)
                    else:
                        read_numbers = True

                found_start += 1
        else:
            read_numbers = False
            if comment.match(line):
                continue
            elif start_value.match(line):
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
                            if not rising_edges.has_key(current_signal_name):
                                rising_edges[current_signal_name] = []
                            rising_edges[current_signal_name].append(time)
                            signal_value = 'F'
                    elif signal_value == 'F':
                        if voltage < fall_th:
                            if not falling_edges.has_key(current_signal_name):
                                falling_edges[current_signal_name] = []
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

    rising_edges,falling_edges = parse_print_file(filename,float(rise_th),float(fall_th))

    import pickle
    with open(filename+'_rising', 'w') as output:
        pickle.dump(rising_edges,output,pickle.HIGHEST_PROTOCOL)
    with open(filename+'_falling', 'w') as output:
        pickle.dump(falling_edges,output,pickle.HIGHEST_PROTOCOL)

