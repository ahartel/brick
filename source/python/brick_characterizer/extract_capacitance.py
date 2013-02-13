
def extract_capacitance(filename,inputs,calibre_bus_delim='<'):
    import re

    caps = {}
    bus = re.compile(r"\[(\d+):(\d+)\]")
    capacitance = re.compile(r"^\d+\s+[\d\.]+\s+([\d\.e\-\+]+)\s+[\d\.]+\s+[\d\.]+\s+(.+)")

    for input in inputs:
        m = bus.search(input)
        if m:
            smaller = int(m.group(1))
            larger = int(m.group(2))
            if smaller >= larger:
                larger,smaller = smaller,larger

            cur_input = ''
            for index in range(smaller,larger+1):
                cur_input = re.sub(r"\[\d+:\d+\]","["+str(index)+"]",input)
                caps[cur_input] = None

        else:
            caps[input] = None

    f = open(filename)
    for line in f:
        m = capacitance.match(line)
        if m:
            net_name = m.group(2)
            if calibre_bus_delim is '<':
                net_name = net_name.replace('<','[')
                net_name = net_name.replace('>',']')

            if caps.has_key(net_name):
                caps[net_name] = float(m.group(1))
    f.close()

    for net,value in caps.iteritems():
        if not value:
            raise Exception('Capacitance for input net '+net+' not found!')

    return caps
