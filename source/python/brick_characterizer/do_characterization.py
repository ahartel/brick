import logging
from multiprocessing import Pool
import threading
sh_lock = threading.Lock()
dt_lock = threading.Lock()

caps = {}
setups = {}
holds = {}
delays = {}
transitions = {}

def start_setup_hold_thread(run,constraint_template):
    global sh_lock
    global setups
    global holds

    logging.info("Starting thread for "+run.whats_my_name())
    OK = True
    while run.has_steps():
        if not run.next_step() == 0:
            OK = False
            break

    if OK == False:
        logging.error("Setup/Hold thread "+run.whats_my_name()+" failed.")
        return 1
    else:
        logging.info("Thread "+run.whats_my_name()+' terminated successfully.')
        logging.debug("Getting rise time values from thread "+run.whats_my_name()+": "+str(run.get_clock_rise_time())+", "+str(run.get_signal_rise_time()))

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

        #logging.debug("Setups for thread "+run.whats_my_name()+": "+str(setups)+", holds: "+str(holds))
        sh_lock.release()
        logging.debug("Setup/Hold time merging lock for thread "+run.whats_my_name()+" released.")


        return 0

def start_delay_thread(run,delay_template):
    global dt_lock
    global delays
    global transitions

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
        logfile,
        parasitics_report=None,
        only_rewrite_lib_file=False,
        skip_setup_hold=False,
        skip_delays=False,
        use_spectre=False,
        additional_probes={},
        default_max_transition=0.2):

    import os
    import logging
    import datetime

    logging.basicConfig(filename=logfile,level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("####################################")
    logging.info("BrickCharacterizer")
    logging.info("####################################")
    logging.info("Logging to "+logfile)
    logging.info("Working directory is "+os.getcwd())
    logging.info("Invoked with the following parameters:")
    logging.info(" only_rewrite_lib_file = "+str(only_rewrite_lib_file))
    logging.info(" skip_setup_hold       = "+str(skip_setup_hold))
    logging.info(" skip_delays           = "+str(skip_delays))
    logging.info("####################################")

    global caps
    global delays
    global transitions
    global setups
    global holds

    setup_hold_failed = False
    delay_failed = False

    if not only_rewrite_lib_file:
        #
        # extract input capacitances
        #
        if parasitics_report:
            from brick_characterizer.extract_capacitance import extract_capacitance
            caps = extract_capacitance(parasitics_report,inputs,inouts)
            logging.info("Using parasitics report in "+parasitics_report)
        else:
            import pickle,os
            if os.path.exists(lib_name+'_'+cell_name+'_input_capacitance.dat'):
                logging.info("Loading previously stored parasitics data from "+lib_name+'_'+cell_name+'_input_capacitance.dat')
                with open(lib_name+'_'+cell_name+'_input_capacitance.dat') as input:
                    caps = pickle.load(input)
            else:
                logging.info("Not using parasitics data!")

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
                print "Loading "+lib_name+'_'+cell_name+'_setups.dat'
                with open(lib_name+'_'+cell_name+'_setups.dat') as input:
                    setups = pickle.load(input)

            if os.path.exists(lib_name+'_'+cell_name+'_holds.dat'):
                print "Loading "+lib_name+'_'+cell_name+'_holds.dat'
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
        if not skip_setup_hold:
            from brick_characterizer.SetupHold_Char import SetupHold_Char

            setups = {}
            holds = {}
            setup_hold_runs = []

            for i in range(len(constraint_template[0])):
                for j in range(len(constraint_template[1])):
                    setup_hold_runs.append(SetupHold_Char(cell_name,output_netlist_file,use_spectre))
                    setup_hold_runs[len(setup_hold_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        setup_hold_runs[len(setup_hold_runs)-1].add_include_netlist(netlist)
                    setup_hold_runs[len(setup_hold_runs)-1].add_static_signals(static_signals)
                    setup_hold_runs[len(setup_hold_runs)-1].add_timing_signals(clocks,input_timing_signals)
                    setup_hold_runs[len(setup_hold_runs)-1].add_additional_probes(additional_probes)

                    setup_hold_runs[len(setup_hold_runs)-1].set_clock_rise_time(constraint_template[0][i])
                    setup_hold_runs[len(setup_hold_runs)-1].set_signal_rise_time(constraint_template[1][j])


            pool = Pool(processes=9)
            results = []
            for run in setup_hold_runs:
                print "Appending job "+run.whats_my_name()+" to Pool"
                results.append(pool.apply_async(start_setup_hold_thread,(run,constraint_template)))

            pool.close()
            pool.join()

            setup_hold_failed = False
            for res in results:
                if not res.get() == 0:
                    setup_hold_failed = True
                    print "Setup/Hold timing characterization failed because one of the threads return non-zero."
                    break

        if not skip_delays and not setup_hold_failed:
            from brick_characterizer.CellRiseFall_Char import CellRiseFall_Char

            delay_runs = []
            delays = {}
            transitions = {}

            for i in range(len(delay_template[0])):
                for j in range(len(delay_template[1])):
                    delay_runs.append(CellRiseFall_Char(cell_name,output_netlist_file,use_spectre))
                    delay_runs[len(delay_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        delay_runs[len(delay_runs)-1].add_include_netlist(netlist)
                    delay_runs[len(delay_runs)-1].add_static_signals(static_signals)
                    delay_runs[len(delay_runs)-1].add_timing_signals(clocks,output_timing_signals)
                    delay_runs[len(delay_runs)-1].add_pseudo_static_signals(input_timing_signals)

                    delay_runs[len(delay_runs)-1].set_input_rise_time(delay_template[0][i])
                    delay_runs[len(delay_runs)-1].set_load_capacitance(delay_template[1][j])


            pool = Pool(processes=9)
            results = []
            for run in delay_runs:
                print "Appending job "+run.whats_my_name()+" to Pool"
                results.append(pool.apply_async(start_delay_thread,(run,delay_template)))

            pool.close()
            pool.join()

            delay_failed = False
            for res in results:
                if not res.get() == 0:
                    delay_failed = True
                    print "Delay timing characterization failed because one of the threads return non-zero."
                    break

        import pickle
        # save setup and hold results for later re-writing of lib files
        if not setup_hold_failed:
            with open(lib_name+'_'+cell_name+'_setups.dat', 'w') as output:
                pickle.dump(setups,output,pickle.HIGHEST_PROTOCOL)
            with open(lib_name+'_'+cell_name+'_holds.dat', 'w') as output:
                pickle.dump(holds,output,pickle.HIGHEST_PROTOCOL)

        # save delay and output transition timings for later re-writing of lib files
        if not delay_failed:
            with open(lib_name+'_'+cell_name+'_delays.dat', 'w') as output:
                pickle.dump(delays,output,pickle.HIGHEST_PROTOCOL)
            with open(lib_name+'_'+cell_name+'_output_transitions.dat', 'w') as output:
                pickle.dump(transitions,output,pickle.HIGHEST_PROTOCOL)

        with open(lib_name+'_'+cell_name+'_input_capacitance.dat', 'w') as output:
            pickle.dump(caps,output,pickle.HIGHEST_PROTOCOL)

    else:
        import pickle
        # load setup and hold results for re-writing of lib files
        with open(lib_name+'_'+cell_name+'_setups.dat') as input:
            setups = pickle.load(input)
        with open(lib_name+'_'+cell_name+'_holds.dat') as input:
            holds = pickle.load(input)

        # save setup and hold results for later re-writing of lib files
        with open(lib_name+'_'+cell_name+'_delays.dat') as input:
            delays = pickle.load(input)
        with open(lib_name+'_'+cell_name+'_output_transitions.dat') as input:
            transitions = pickle.load(input)

        with open(lib_name+'_'+cell_name+'_input_capacitance.dat') as input:
            caps = pickle.load(input)

    #
    # Write lib file
    #
    if not setup_hold_failed and not delay_failed:
        from brick_characterizer.LibBackend import LibBackend
        be = LibBackend(constraint_template,delay_template,default_max_transition)
        be.write(lib_name,cell_name,output_lib_file,inputs,outputs,inouts,powers,caps,clocks,input_timing_signals,output_timing_signals,setups,holds,delays,transitions)
    else:
        print "Not writing .lib file because setup/hold or delay calculation had an error."
        return 1
