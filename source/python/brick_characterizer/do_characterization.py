import threading
inc_lock = threading.Lock()
sh_lock = threading.Lock()
dt_lock = threading.Lock()

threads_running = 0
max_threads = 8

setups = {}
holds = {}
delays = {}
transitions = {}

def start_setup_hold_thread(run,constraint_template):
    global max_threads
    global inc_lock
    global sh_lock
    global threads_running
    global setups
    global holds
    from time import sleep

    while not threads_running < max_threads:
        sleep(1)
    inc_lock.acquire()
    threads_running += 1
    inc_lock.release()

    print "Starting thread for "+run.whats_my_name()
    while run.has_steps():
        run.next_step()
    print "thread "+run.whats_my_name()+' done'

    this_setups = run.get_setups()
    this_holds = run.get_holds()
    sh_lock.acquire()
    for signal,values in this_setups.iteritems():
        if not setups.has_key(signal):
            setups[signal] = {}
            for tran in constraint_template[0]:
                setups[signal][tran] = {}

        setups[signal][run.get_clock_rise_time()][run.get_signal_rise_time()] = values

    for signal,values in this_holds.iteritems():
        if not holds.has_key(signal):
            holds[signal] = {}
            for tran in constraint_template[0]:
                holds[signal][tran] = {}

        holds[signal][run.get_clock_rise_time()][run.get_signal_rise_time()] = values

    sh_lock.release()

    inc_lock.acquire()
    threads_running -= 1
    inc_lock.release()

def start_delay_thread(run,delay_template):
    global threads_running
    global max_threads
    global inc_lock
    global dt_lock
    global delays
    global transitions
    from time import sleep

    while not threads_running < max_threads:
        sleep(1)
    inc_lock.acquire()
    threads_running += 1
    inc_lock.release()

    print "Starting thread for "+run.whats_my_name()
    while run.has_steps():
        run.next_step()
    print "thread "+run.whats_my_name()+' done'

    this_delays = run.get_delays()
    this_transitions = run.get_transitions()
    dt_lock.acquire()
    for signal,values in this_delays.iteritems():
        if not delays.has_key(signal):
            delays[signal] = {}
            for tran in delay_template[0]:
                delays[signal][tran] = {}

        delays[signal][run.get_input_rise_time()][run.get_load_capacitance()] = values

    for signal,values in this_transitions.iteritems():
        if not transitions.has_key(signal):
            transitions[signal] = {}
            for tran in delay_template[0]:
                transitions[signal][tran] = {}

        transitions[signal][run.get_input_rise_time()][run.get_load_capacitance()] = values
    dt_lock.release()

    inc_lock.acquire()
    threads_running -= 1
    inc_lock.release()



def do_characterization(
        lib_name,
        cell_name,
        output_lib_file,
        output_netlist_file,
        inc_netlists,
        inputs,
        outputs,
        inouts,
        powers,
        static_signals,
        clocks,
        input_timing_signals,
        output_timing_signals,
        constraint_template,
        delay_template,
        only_rewrite_lib_file,
        skip_setup_hold,
        skip_delays):

    import logging
    import datetime

    logging.basicConfig(filename='./logfiles/brick_characterize_'+cell_name+'_'+str(datetime.datetime.now())+'.log',level=logging.DEBUG,format='%(asctime)s %(message)s')

    #
    # extract input capacitances
    #
    from brick_characterizer.extract_capacitance import extract_capacitance
    caps = extract_capacitance('build/results/'+cell_name+'.pex.report',inputs,inouts)

    global delays
    global transitions
    global setups
    global holds


    if not only_rewrite_lib_file:

        if not input_timing_signals or len(input_timing_signals) == 0:
            skip_setup_hold = True
        else:
            if not clocks or len(clocks) == 0:
                raise Exception('No clocks defined')

        if not output_timing_signals or len(output_timing_signals) == 0:
            skip_delays = True
        else:
            if not clocks or len(clocks) == 0:
                raise Exception('No clocks defined')


        # load setup and hold results for re-writing of lib files
        if skip_setup_hold:
            import pickle,os
            if os.path.exists(lib_name+'_'+cell_name+'_setups.dat'):
                with open(lib_name+'_'+cell_name+'_setups.dat') as input:
                    setups = pickle.load(input)

            if os.path.exists(lib_name+'_'+cell_name+'_holds.dat'):
                with open(lib_name+'_'+cell_name+'_holds.dat') as input:
                    holds = pickle.load(input)

        # save setup and hold results for later re-writing of lib files
        if skip_delays:
            import pickle,os
            if os.path.exists(lib_name+'_'+cell_name+'_delays.dat'):
                print "Loading "+lib_name+'_'+cell_name+'_delays.dat'
                with open(lib_name+'_'+cell_name+'_delays.dat') as input:
                    delays = pickle.load(input)
            if os.path.exists(lib_name+'_'+cell_name+'_output_transitions.dat'):
                print "Loading "+lib_name+'_'+cell_name+'_output_transitions.dat'
                with open(lib_name+'_'+cell_name+'_output_transitions.dat') as input:
                    transitions = pickle.load(input)

        # characterize setup & hold timing
        if skip_setup_hold:
            setups = {}
            holds = {}
        else:
            from brick_characterizer.SetupHold_Char import SetupHold_Char

            setups = {}
            holds = {}
            setup_hold_runs = []

            for i in range(len(constraint_template[0])):
                for j in range(len(constraint_template[1])):
                    setup_hold_runs.append(SetupHold_Char(cell_name,output_netlist_file))
                    setup_hold_runs[len(setup_hold_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        setup_hold_runs[len(setup_hold_runs)-1].add_include_netlist(netlist)
                    setup_hold_runs[len(setup_hold_runs)-1].add_static_signals(static_signals)
                    setup_hold_runs[len(setup_hold_runs)-1].add_timing_signals(clocks,input_timing_signals)

                    setup_hold_runs[len(setup_hold_runs)-1].set_clock_rise_time(constraint_template[0][i])
                    setup_hold_runs[len(setup_hold_runs)-1].set_signal_rise_time(constraint_template[1][j])


            run_cnt = 0

            t = []

            for run in setup_hold_runs:
                print run.whats_my_name()
                t.append(threading.Thread(target=start_setup_hold_thread,args=(run,constraint_template)))
                t[len(t)-1].start()
                run_cnt += 1

            print "added "+str(run_cnt)+" threads"

            for thread in t:
                if thread.is_alive():
                    thread.join()


        if skip_delays:
            delays = {}
            transitions = {}
        else:
            from brick_characterizer.CellRiseFall_Char import CellRiseFall_Char

            delay_runs = []
            delays = {}
            transitions = {}

            for i in range(len(delay_template[0])):
                for j in range(len(delay_template[1])):
                    delay_runs.append(CellRiseFall_Char(cell_name,output_netlist_file))
                    delay_runs[len(delay_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        delay_runs[len(delay_runs)-1].add_include_netlist(netlist)
                    delay_runs[len(delay_runs)-1].add_static_signals(static_signals)
                    delay_runs[len(delay_runs)-1].add_timing_signals(clocks,output_timing_signals)
                    delay_runs[len(delay_runs)-1].add_pseudo_static_signals(input_timing_signals)

                    delay_runs[len(delay_runs)-1].set_input_rise_time(delay_template[0][i])
                    delay_runs[len(delay_runs)-1].set_load_capacitance(delay_template[1][j])


            run_cnt = 0

            t = []

            for run in delay_runs:
                print run.whats_my_name()
                t.append(threading.Thread(target=start_delay_thread,args=(run,delay_template)))
                t[len(t)-1].start()
                run_cnt += 1

            print "added "+str(run_cnt)+" threads"

            for thread in t:
                if thread.is_alive():
                    thread.join()

        # save setup and hold results for later re-writing of lib files
        import pickle
        with open(lib_name+'_'+cell_name+'_setups.dat', 'w') as output:
            pickle.dump(setups,output,pickle.HIGHEST_PROTOCOL)
        with open(lib_name+'_'+cell_name+'_holds.dat', 'w') as output:
            pickle.dump(holds,output,pickle.HIGHEST_PROTOCOL)

        # save setup and hold results for later re-writing of lib files
        import pickle
        with open(lib_name+'_'+cell_name+'_delays.dat', 'w') as output:
            pickle.dump(delays,output,pickle.HIGHEST_PROTOCOL)
        with open(lib_name+'_'+cell_name+'_output_transitions.dat', 'w') as output:
            pickle.dump(transitions,output,pickle.HIGHEST_PROTOCOL)
    else:
        # load setup and hold results for re-writing of lib files
        import pickle
        with open(lib_name+'_'+cell_name+'_setups.dat') as input:
            setups = pickle.load(input)
        with open(lib_name+'_'+cell_name+'_holds.dat') as input:
            holds = pickle.load(input)

        # save setup and hold results for later re-writing of lib files
        import pickle
        with open(lib_name+'_'+cell_name+'_delays.dat') as input:
            delays = pickle.load(input)
        with open(lib_name+'_'+cell_name+'_output_transitions.dat') as input:
            transitions = pickle.load(input)

    #
    # Write lib file
    #

    from brick_characterizer.LibBackend import LibBackend
    be = LibBackend(constraint_template,delay_template)
    be.write(lib_name,cell_name,output_lib_file,inputs,outputs,inouts,powers,caps,input_timing_signals,output_timing_signals,setups,holds,delays,transitions)


