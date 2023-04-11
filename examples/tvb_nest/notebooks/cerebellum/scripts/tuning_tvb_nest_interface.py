from examples.tvb_nest.notebooks.cerebellum.scripts.tvb_nest_script import *
from tvb_multiscale.core.plot.plotter import Plotter

# Choose interface parameters
# NB: it could be a factor for G!! Explore a bit this or put as a multiplicative factor of G

# Run the cosimulation
# results, transient, simulator, nest_network, PSD = run_tvb_nest_workflow(model_params = {'G':1}) - not working: TO FIX
from examples.tvb_nest.notebooks.cerebellum.scripts.nest_script import build_NEST_network, plot_nest_results_raster

model_params = {'STIMULUS': 5.0, 'G': 6}        # Tuning is done at baseline

tuned_values = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]

tuned_value = 0.1

# Get configuration
config, plotter = configure(output_folder=str(tuned_value)+'_stimON_5', verbose=2)
print("config.NEST_PERIPHERY",config.NEST_PERIPHERY)
config.model_params.update(model_params)
config.SIMULATION_LENGTH = 10000
config.TRANSIENT_RATIO = 0.5
# Load and prepare connectome and connectivity with all possible normalizations:
connectome, major_structs_labels, voxel_count, inds, maps = prepare_connectome(config, plotter=plotter)
connectivity = build_connectivity(connectome, inds, config)
# Prepare model
model = build_model(connectivity.number_of_regions, inds, maps, config)
# Prepare simulator
simulator = build_simulator(connectivity, model, inds, maps, config, plotter=plotter)
# Build TVB-NEST interfaces
nest_network, nest_nodes_inds, neuron_models, neuron_number = build_NEST_network(config)
simulator, nest_network = build_tvb_nest_interfaces(simulator, nest_network, nest_nodes_inds, config, tvb_to_nest_gain=tuned_value)
# Simulate TVB-NEST model
results, transient, simulator, nest_network = simulate_tvb_nest(simulator, nest_network, config)

       
# Plot results
# plot_tvb(transient, inds, results=results,
#            source_ts=None, bold_ts=None, PSD_target=PSD_target, PSD=PSD,
#            simulator=simulator, plotter=plotter, config=config, write_files=True)
# plot_nest_results(nest_network, neuron_models, neuron_number, config)

# Get spike events from NEST spike recorders
events = nest_network.output_devices['mossy_fibers']['Right Ansiform lobule'].get_events()

# Compute approximate average rate of mossy fibers as:
# number_of_spikes / (number_of_neurons * time_length_in_ms) * 1000 (to convert to spikes/sec)
duration = config.SIMULATION_LENGTH
n_spikes = np.sum(events['times'] > events['times'][-1] - duration)
print("Approximate mossy_fibers rate during the last %g ms = %g" % 
      (duration, n_spikes / 
                  (nest_network.output_devices['mossy_fibers']['Right Ansiform lobule'].number_of_neurons 
                   * duration) * 1000))

            
# Add functions from NEST               