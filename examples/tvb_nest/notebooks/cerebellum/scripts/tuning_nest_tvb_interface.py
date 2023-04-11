from examples.tvb_nest.notebooks.cerebellum.scripts.tvb_nest_script import *
from tvb_multiscale.core.plot.plotter import Plotter
from tvb.contrib.scripts.datatypes.time_series_xarray import TimeSeriesRegion as TimeSeriesXarray

from examples.tvb_nest.notebooks.cerebellum.scripts.nest_script import *        #build_NEST_network, plot_nest_results

model_params = {'STIMULUS': 0.0, 'G': 6}        # Tuning is done at baseline

tuned_values_tvb_nest = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]

tuned_values_nest_tvb = [100, 150]

tuned_value_nest_tvb = 50 
tuned_value_tvb_nest = 0.1          #0.8 
COMPUTE_REF = True

# Get configuration
config, plotter = configure(output_folder='nest_tvb_'+str(tuned_value_nest_tvb)+'_', verbose=2)
print("config.NEST_PERIPHERY",config.NEST_PERIPHERY)
config.model_params.update(model_params)
config.SIMULATION_LENGTH = 100            #250
config.TRANSIENT_RATIO = 0.5
# Load and prepare connectome and connectivity with all possible normalizations:
connectome, major_structs_labels, voxel_count, inds, maps = prepare_connectome(config, plotter=plotter)
connectivity = build_connectivity(connectome, inds, config)
# Prepare model
model = build_model(connectivity.number_of_regions, inds, maps, config)
# Prepare simulator
simulator = build_simulator(connectivity, model, inds, maps, config, plotter=plotter)
if COMPUTE_REF:
    # Run simulation and get results for reference values
    results, transient = simulate(simulator, config)
else:
    # Build TVB-NEST interfaces
    nest_network, nest_nodes_inds, neuron_models, neuron_number = build_NEST_network(config)
    simulator, nest_network = build_tvb_nest_interfaces(simulator, nest_network, nest_nodes_inds, config, max_rate_to_tune=tuned_value_nest_tvb)
    # Simulate TVB-NEST model
    results, transient, simulator, nest_network = simulate_tvb_nest(simulator, nest_network, config)
        
print(results)

# Save results
results = tvb_res_to_time_series(results, simulator, config=config, write_files=True)

# Compute baseline of TVB regions of interest
regs = ['ansilob', 'interposed', 'oliv']            # L and R ? 

# results=None

source_ts = plot_tvb(transient, inds, results=results, source_ts=None, bold_ts=None,
                    simulator=simulator, plotter=plotter, config=config, write_files=True)[0]


if results is not None:
    source_ts = TimeSeriesXarray(  # substitute with TimeSeriesRegion fot TVB like functionality
            data=results[0][1], time=results[0][0],
            connectivity=simulator.connectivity,
            labels_ordering=["Time", "State Variable", "Region", "Neurons"],
            labels_dimensions={"State Variable": list(simulator.model.variables_of_interest),
                               "Region": simulator.connectivity.region_labels.tolist()},
            sample_period=simulator.integrator.dt)
    source_ts.configure()

    t = source_ts.time
    

source_ts_interface = {}
print(inds.keys(), inds['oliv'])
if source_ts is not None:
    for reg in regs:
        source_ts_interface[reg] = source_ts[-config.SIMULATION_LENGTH:, 0, inds[reg][1]]
        print("source ts shape ", source_ts_interface[reg])
        print("source ts parts", source_ts_interface[reg].Time, source_ts_interface[reg].values)
        print("Avg baseline for ", reg, np.mean(source_ts_interface[reg]))
        
        
# Target values: ansilob=-0.3263, interposed=-0.3209, oliv=-0.3284


