#
# configuration
#
rise_threshold = 0.5
fall_threshold = 0.5

inputs = [
    'w_addr_pre[5:0]',
    'w_addr_pst[7:0]',
    'pc_conf_pst[7:0]',
    'pc_conf_pre[3:0]',
    'w_conf_pst[15:0]',
    'w_conf_pre[7:0]',
    'write_pst',
    'write_pre',
    'en_pre',
    'en_pst',
    'write_sel_pst[3:0]',
    'write_sel_pre[31:0]',
    'd_in_pre[255:0]',
    'd_in_pst[31:0]',
    ]

outputs = [
    'd_out_pst[31:0]',
    'd_out_pre[255:0]',
    ]

static_signals = {
    'w_addr_pre[5:0]': 0,
    'w_addr_pst[7:0]': 0,
    'pc_conf_pst[7:0]': 0,
    'pc_conf_pre[3:0]': 0,
    'w_conf_pst[15:0]': 0,
    'w_conf_pre[7:0]': 0,
    'write_pst': 0,
    'write_pre': 0,
    'en_pre': 0,
    }

powers = {
    'vdd12d': 1.2,
    'gndd': 0,
    }

clocks = { 'clk_pst': 'R', 'clk_pre': 'R' }

timing_signals = {
        'write_sel_pst[3:0]': ['clk_pst', 'N_Xrow_driver[=index=]_net06_Xrow_driver[=index=]_MM27_g', 'positive_unate'],
        #'write_sel_pre[31:0]': ['clk_pre', 'N_Xcol_driver[=index=]_net346_Xcol_driver[=index=]_MM26_g', 'positive_unate'],
        #'d_in_pst[31:0]' : ['clk_pst', 'N_Xrow_driver[=index/8=]_Xdriver_pst[=index%8=]_net043_Xrow_driver[=index/8=]_Xdriver_pst[=index%8=]_XI5_MM42_g', 'positive_unate'],
        #'d_in_pre[255:0]' : ['clk_pre', 'N_Xcol_driver[=index/8=]_Xdriver_pre[=index%8=]_net047_Xcol_driver[=index/8=]_Xdriver_pre[=index%8=]_XI5_MM42_g', 'positive_unate'],
        'en_pst': ['clk_pst','N_Xtiming_Xtiming_pst_en_int_Xtiming_Xtiming_pst_XI3_MM122_g','positive_unate']
    }


circuit_netlist_path = "./build/results/SRAM_top.pex.netlist"
model_netlist_path = '../../env/include_all_models.scs'

char_output_file = './netlists/char_SRAM_top.sp'

output_lib_file = './analog_top_tb_SRAM_top.lib'

constraint_template = [
    # related_pin_tranisition (ns)
    [0.1,0.2,0.3],
    # constrainted_pin_tranisition (ns)
    [0.1,0.2,0.3],
]

#
# end of configuration
#

# extract input capacitances

from brick_characterizer.extract_capacitance import extract_capacitance
caps = extract_capacitance('build/results/SRAM_top.pex.report',inputs)

# characterize setup & hold timing

from brick_characterizer.SimulationRunV2 import SimulationRun

# only one run for now
# later loop over constraints

runs = []
setups = {}
holds = {}

import copy

#for i in range(len(constraint_template[0])):
#    for j in range(len(constraint_template[1])):
if 1:
        i = 0
        j = 0
        runs.append(SimulationRun('SRAM_top',char_output_file))
        runs[len(runs)-1].set_powers(powers)
        runs[len(runs)-1].add_include_netlist(circuit_netlist_path)
        runs[len(runs)-1].add_include_netlist(model_netlist_path)
        runs[len(runs)-1].add_static_signals(static_signals)
        runs[len(runs)-1].add_timing_signals(clocks,timing_signals)

        runs[len(runs)-1].set_clock_rise_time(constraint_template[0][i])
        runs[len(runs)-1].set_signal_rise_time(constraint_template[1][j])


import threading
from time import sleep
max_threads = 7
threads_running = 0
run_cnt = 0
inc_lock = threading.Lock()

def start_thread(run):
    global threads_running
    global max_threads
    global inc_lock

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

    inc_lock.acquire()
    threads_running -= 1
    inc_lock.release()

t = []

for run in [runs[0]]:
    print run.whats_my_name()
    t.append(threading.Thread(target=start_thread,args=(run,)))
    t[len(t)-1].start()
    run_cnt += 1

print "added "+str(run_cnt)+" threads"

for thread in t:
    if thread.is_alive():
        thread.join()

print setups
print holds

#setups['en_pst'] = {}
#setups['write_sel_pst[3]'] = {}
#holds['en_pst'] = {}
#holds['write_sel_pst[3]'] = {}
#for i in range(3):
#    setups['en_pst'][constraint_template[0][i]] = {}
#    setups['write_sel_pst[3]'][constraint_template[0][i]] = {}
#    holds['en_pst'][constraint_template[0][i]] = {}
#    holds['write_sel_pst[3]'][constraint_template[0][i]] = {}
#    for j in range(3):
#        setups['en_pst'][constraint_template[0][i]][constraint_template[1][j]] = [0.1,0.2]
#        setups['write_sel_pst[3]'][constraint_template[0][i]][constraint_template[1][j]] = [0.1,0.2]
#        holds['en_pst'][constraint_template[0][i]][constraint_template[1][j]] = [0.1,0.2]
#        holds['write_sel_pst[3]'][constraint_template[0][i]][constraint_template[1][j]] = [0.1,0.2]

from brick_characterizer.LibBackend import LibBackend
be = LibBackend(constraint_template)
be.write('route65','SRAM_top',output_lib_file,inputs,outputs,powers,caps,timing_signals,setups,holds)

