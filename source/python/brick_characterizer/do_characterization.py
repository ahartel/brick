import threading
inc_lock = threading.Lock()
sh_lock = threading.Lock()
dt_lock = threading.Lock()

threads_running = 0
max_threads = 5

setups = {}
holds = {}
delays = {}
transitions = {}

def start_setup_hold_thread(run):
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

def start_delay_thread(run):
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

    #this_setups = run.get_setups()
    #this_holds = run.get_holds()
    dt_lock.acquire()
    #for signal,values in this_setups.iteritems():
    #    if not setups.has_key(signal):
    #        setups[signal] = {}
    #        for tran in constraint_template[0]:
    #            setups[signal][tran] = {}

    #    setups[signal][run.get_clock_rise_time()][run.get_signal_rise_time()] = values

    #for signal,values in this_holds.iteritems():
    #    if not holds.has_key(signal):
    #        holds[signal] = {}
    #        for tran in constraint_template[0]:
    #            holds[signal][tran] = {}

    #    holds[signal][run.get_clock_rise_time()][run.get_signal_rise_time()] = values
    dt_lock.release()

    inc_lock.acquire()
    threads_running -= 1
    inc_lock.release()



def do_characterization(lib_name,cell_name,output_lib_file,output_netlist_file,inc_netlists,inputs,outputs,powers,static_signals,clocks,input_timing_signals,output_timing_signals,constraint_template,delay_template,only_rewrite_lib_file,skip_setup_hold,skip_delays):

    import logging
    import datetime

    logging.basicConfig(filename='./logfiles/brick_characterize_'+cell_name+'_'+str(datetime.datetime.now())+'.log',level=logging.DEBUG,format='%(asctime)s %(message)s')

    #
    # extract input capacitances
    #
    from brick_characterizer.extract_capacitance import extract_capacitance
    caps = extract_capacitance('build/results/'+cell_name+'.pex.report',inputs)

    if not only_rewrite_lib_file:

        from brick_characterizer.SetupHold_Char import SetupHold_Char
        from brick_characterizer.CellRiseFall_Char import CellRiseFall_Char

        # characterize setup & hold timing
        if skip_setup_hold:
            setups = {}
            holds = {}
        else:
            setups = {}
            holds = {}
            setup_hold_runs = []

            import copy

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
                t.append(threading.Thread(target=start_setup_hold_thread,args=(run,)))
                t[len(t)-1].start()
                run_cnt += 1

            print "added "+str(run_cnt)+" threads"

            for thread in t:
                if thread.is_alive():
                    thread.join()

            # save setup and hold results for later re-writing of lib files
            import pickle
            with open(cell_name+'_setups.dat', 'w') as output:
                pickle.dump(setups,output,pickle.HIGHEST_PROTOCOL)
            with open(cell_name+'_holds.dat', 'w') as output:
                pickle.dump(holds,output,pickle.HIGHEST_PROTOCOL)

        if skip_delays:
            delays = {}
            transitions = {}
        else:
            delay_runs = []
            delays = {}
            transitions = {}

            import copy

            for i in range(len(delay_template[0])):
                for j in range(len(delay_template[1])):
                    delay_runs.append(CellRiseFall_Char(cell_name,output_netlist_file))
                    delay_runs[len(delay_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        delay_runs[len(delay_runs)-1].add_include_netlist(netlist)
                    delay_runs[len(delay_runs)-1].add_static_signals(static_signals)
                    delay_runs[len(delay_runs)-1].add_pseudo_static_signals(input_timing_signals)
                    delay_runs[len(delay_runs)-1].add_timing_signals(clocks,output_timing_signals)

                    delay_runs[len(delay_runs)-1].set_input_rise_time(delay_template[0][i])
                    delay_runs[len(delay_runs)-1].set_load_capacitance(delay_template[1][j])


            run_cnt = 0

            t = []

            for run in delay_runs:
                print run.whats_my_name()
                t.append(threading.Thread(target=start_delay_thread,args=(run,)))
                t[len(t)-1].start()
                run_cnt += 1

            print "added "+str(run_cnt)+" threads"

            for thread in t:
                if thread.is_alive():
                    thread.join()

            # save setup and hold results for later re-writing of lib files
            #import pickle
            #with open('setups.dat', 'w') as output:
            #    pickle.dump(setups,output,pickle.HIGHEST_PROTOCOL)
            #with open('holds.dat', 'w') as output:
            #    pickle.dump(holds,output,pickle.HIGHEST_PROTOCOL)
    else:
        # load setup and hold results for re-writing of lib files
        import pickle
        with open(cell_name+'_setups.dat') as input:
            setups = pickle.load(input)
        with open(cell_name+'_holds.dat') as input:
            holds = pickle.load(input)


    #
    # Write lib file
    #

    from brick_characterizer.LibBackend import LibBackend
    be = LibBackend(constraint_template)
    be.write(lib_name,cell_name,output_lib_file,inputs,outputs,powers,caps,input_timing_signals,setups,holds)


