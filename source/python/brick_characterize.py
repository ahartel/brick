#
# configuration
#
rise_threshold = 0.5
fall_threshold = 0.5

static_signals = {
    'str': 0,
    'addr[5:0]': 0,
    'd_in_pst[7:0]': 0,
    'write_en_pst': 0,
    'sense_pst': 0,
    'pc_pst': 0,
    'wen_pre': 0,
    }

powers = {
    'vdd': 1.2,
    'gnd': 0,
    }

clock = [ 'clk', 'R']

timing_signals = {
        'write_sel_pst': 'R'
    }

probe_signals = {
        'XI0_net06': 'write_sel_pst',
    }

probe_signal_directions = {
        'XI0_net06': 'R'
    }

circuit_netlist_path = "/superfast/home/ahartel/chip-route65/rundirs/libgen_sram_ff/build/results/sram_flip_flops_pst.pex.netlist"
model_netlist_path = 'models.sp'

output_file = 'brick_analysis.sp'

constraint_template = [
    # related_pin_tranisition (ns)
    [0.1,0.2,0.3],
    # constrainted_pin_tranisition (ns)
    [0.1,0.2,0.3],
]

#
# end of configuration
#

from SimulationRun import SimulationRun

# only one run for now
# later loop over constraints

run = SimulationRun('sram_flip_flops_pst')
run.add_include_netlist(circuit_netlist_path)
run.add_include_netlist(model_netlist_path)
run.add_static_signals(static_signals)
run.add_timing_signals(clock,timing_signals,probe_signals,probe_signal_directions)
run.write_spice_file(output_file)
run.run()
run.check_timing()

