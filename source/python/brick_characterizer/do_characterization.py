import logging
from time import sleep
from multiprocessing import Pool#, Lock


def start_setup_hold_thread(run):

    logging.info("Starting thread for "+run.whats_my_name())
    OK = True
    while run.has_steps():
        if not run.next_step() == 0:
            OK = False
            break

    if OK == False:
        logging.error("Setup/Hold thread "+run.whats_my_name()+" failed.")
        return (1,None,None)
    else:
        logging.info("Thread "+run.whats_my_name()+' terminated successfully.')
        logging.debug("Getting rise time values from thread "+run.whats_my_name()+": "+str(run.get_clock_rise_time())+", "+str(run.get_signal_rise_time()))

        this_setups = run.get_setups()
        this_holds = run.get_holds()


        return 0,this_setups,this_holds

def start_delay_thread(run):

    print "Starting thread for "+run.whats_my_name()
    OK = True
    while run.has_steps():
        if not run.next_step() == 0:
            OK = False
            break

    if OK == False:
        logging.error("Delay thread "+run.whats_my_name()+" failed.")
        return (1,None,None)
    else:
        print "thread "+run.whats_my_name()+' done'

        this_delays = run.get_delays()
        this_transitions = run.get_transitions()

        return (0,this_delays,this_transitions)


def append_wait_check_pool(size,jobs,function,constraint_template):
    # initialize result structures
    result_tables = [{},{}]
    # create a process pool (limit amount of parallel workers)
    pool = Pool(processes=size)#,initializer=initialize_lock, initargs=(lck,))
    # append a worker for each entry in the list of jobs
    results = []
    for run in jobs:
        print "Appending job "+run.whats_my_name()+" to Pool"
        results.append(pool.apply_async(function,(run,)))
    # don't allow further entries into the pool (this is mandatory for later join())
    pool.close()
    # The while loop polls for the results of the processes
    # This is done because if one thread fails we don't want new
    # processes to be started
    failed = False
    complete = False
    while not complete and not failed:
        complete = True
        for num,res in enumerate(results):
            if res.ready():
                proc_result = res.get()
                # positive results have to be merged into the global structures
                if proc_result[0] == 0:
                    for i in range(2):
                        for signal,values in proc_result[1+i].iteritems():
                            if not result_tables[i].has_key(signal):
                                result_tables[i][signal] = {}
                                for tran in constraint_template[0]:
                                    result_tables[i][signal][tran] = {}

                            result_tables[i][signal][jobs[num].get_first_table_param()][jobs[num].get_second_table_param()] = values

                else:
                    failed = True
                    logging.error("Timing characterization failed because thread "+jobs[num].whats_my_name()+" returned non-zero.")
                    break
            else:
                complete = False
        sleep(1)

    # if one process failed, terminate all others (facilitates debugging)
    if failed:
        pool.terminate()
    # By now (in any case) all processes should already have terminated anyway
    pool.join()

    return (failed,result_tables[0],result_tables[1])

def do_characterization(
        lib_name,
        cell_name,
        output_lib_file,
        output_netlist_file,
        inc_netlists,
        inputs,
        outputs,
        inouts,
        analogs,
        powers,
        static_signals,
        clocks,
        input_timing_signals,
        output_timing_signals,
        constraint_template,
        delay_template,
        logfile,
        temperature,
        parasitics_report=None,
        only_rewrite_lib_file=False,
        skip_setup_hold=False,
        skip_delays=False,
        use_spectre=False,
        additional_probes={},
        default_max_transition=0.7654):

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

    caps = {}
    setups = {}
    holds = {}
    delays = {}
    transitions = {}

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
                    setup_hold_runs.append(SetupHold_Char(cell_name,output_netlist_file,temperature,use_spectre))
                    setup_hold_runs[len(setup_hold_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        setup_hold_runs[len(setup_hold_runs)-1].add_include_netlist(netlist)
                    setup_hold_runs[len(setup_hold_runs)-1].add_static_signals(static_signals)
                    setup_hold_runs[len(setup_hold_runs)-1].add_timing_signals(clocks,input_timing_signals)
                    setup_hold_runs[len(setup_hold_runs)-1].add_additional_probes(additional_probes)

                    setup_hold_runs[len(setup_hold_runs)-1].set_clock_rise_time(constraint_template[0][i])
                    setup_hold_runs[len(setup_hold_runs)-1].set_signal_rise_time(constraint_template[1][j])


            setup_hold_failed,setups,holds = append_wait_check_pool(9,setup_hold_runs,start_setup_hold_thread,constraint_template)


        if not skip_delays and not setup_hold_failed:
            from brick_characterizer.CellRiseFall_Char import CellRiseFall_Char

            delay_runs = []
            delays = {}
            transitions = {}

            for i in range(len(delay_template[0])):
                for j in range(len(delay_template[1])):
                    delay_runs.append(CellRiseFall_Char(cell_name,output_netlist_file,temperature,use_spectre))
                    delay_runs[len(delay_runs)-1].set_powers(powers)
                    for netlist in inc_netlists:
                        delay_runs[len(delay_runs)-1].add_include_netlist(netlist)
                    delay_runs[len(delay_runs)-1].add_static_signals(static_signals)
                    delay_runs[len(delay_runs)-1].add_timing_signals(clocks,output_timing_signals)
                    delay_runs[len(delay_runs)-1].add_pseudo_static_signals(input_timing_signals)

                    delay_runs[len(delay_runs)-1].set_input_rise_time(delay_template[0][i])
                    delay_runs[len(delay_runs)-1].set_load_capacitance(delay_template[1][j])


            delay_failed,delays,transitions = append_wait_check_pool(9,delay_runs,start_delay_thread,delay_template)

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
        logging.info("Writing file "+output_lib_file+".")
        from brick_characterizer.LibBackend import LibBackend
        be = LibBackend(constraint_template,delay_template,default_max_transition)
        be.write(
                lib_name,
                cell_name,
                output_lib_file,
                inputs,
                outputs,
                inouts,
                analogs,
                powers,
                caps,
                clocks,
                input_timing_signals,
                output_timing_signals,
                setups,
                holds,
                delays,
                transitions
            )
        return 0
    else:
        logging.error("Not writing .lib file because setup/hold or delay calculation had an error.")
        return 1
