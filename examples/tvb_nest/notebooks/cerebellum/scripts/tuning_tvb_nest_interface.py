from examples.tvb_nest.notebooks.cerebellum.scripts.tvb_nest_script import *
from tvb_multiscale.core.plot.plotter import Plotter

# Choose interface parameters

config, plotter = configure()

# Run the cosimulation
# results, transient, simulator, nest_network, PSD = run_tvb_nest_workflow(model_params = {'G':1}) - not working: TO FIX
from examples.tvb_nest.notebooks.cerebellum.scripts.nest_script import build_NEST_network, plot_nest_results

model_params = {}
# Get configuration
config, plotter = configure()
config.model_params.update(model_params)
# config.SIMULATION_LENGTH = 100.0
# Load and prepare connectome and connectivity with all possible normalizations:
connectome, major_structs_labels, voxel_count, inds, maps = prepare_connectome(config, plotter=plotter)
connectivity = build_connectivity(connectome, inds, config)
# Prepare model
model = build_model(connectivity.number_of_regions, inds, maps, config)
# Prepare simulator
simulator = build_simulator(connectivity, model, inds, maps, config, plotter=plotter)
# Build TVB-NEST interfaces
nest_network, nest_nodes_inds, neuron_models, neuron_number = build_NEST_network(config)
simulator, nest_network = build_tvb_nest_interfaces(simulator, nest_network, nest_nodes_inds, config)
# Simulate TVB-NEST model
results, transient, simulator, nest_network = simulate_tvb_nest(simulator, nest_network, config)
if PSD_target is None:
    # This is the PSD target we are trying to fit:
    PSD_target = compute_target_PSDs(config, write_files=True, plotter=plotter)
# This is the PSD computed from our simulation results.
PSD = compute_data_PSDs(results[0], PSD_target, inds, transient, plotter=plotter)
# Plot results
if config_args.get('plot_flag', True):
    plot_tvb(transient, inds, results=results,
                source_ts=None, bold_ts=None, PSD_target=PSD_target, PSD=PSD,
                simulator=simulator, plotter=plotter, config=config, write_files=True)
    plot_nest_results(nest_network, neuron_models, neuron_number, config)

# Evaluate MF and IO firing rate: it should be 4 Hz for MFs and 0 Hz for IOs
spikeNet_analyzer = None
if nest_network is not None:
    from tvb_multiscale.core.data_analysis.spiking_network_analyser import SpikingNetworkAnalyser
    # Create a SpikingNetworkAnalyzer:
    spikeNet_analyzer = \
        SpikingNetworkAnalyser(spikeNet=nest_network,
                               start_time=0.0, end_time=500, 
                               transient=transient, time_series_output_type="TVB", 
                               return_data=True, force_homogeneous_results=True, 
                               period=simulator.monitors[0].period, connectivity=simulator.connectivity
                              )
spikes_res = None

if spikeNet_analyzer is not None:
    
    # Spikes rates and correlations per Population and Region
    spikes_res = \
        spikeNet_analyzer.\
            compute_spikeNet_spikes_rates_and_correlations(
                populations_devices=None, regions=None,
                rates_methods=[], rates_kwargs=[{}],rate_results_names=[],
                corrs_methods=[], corrs_kwargs=[{}], corrs_results_names=[], bin_kwargs={},
                data_method=spikeNet_analyzer.get_spikes_from_device, data_kwargs={},
                return_devices=False
            );

if spikes_res:
    print(spikes_res["mean_rate"])
    print(spikes_res["spikes_correlation_coefficient"])
    # Plot spikes' rasters together with mean population's spikes' rates' time series
    
    if plotter:
        plotter.plot_spike_events(spikes_res["spikes"], mean_results=spikes_res["mean_rate"], # time_series=spikes_res["mean_rate_time_series"], 
                                  figsize=(20, 22),  
                                  stimulus=None,
                                  stimulus_linewidth=5.0,
                                  spikes_markersize=5.0, spikes_alpha=0.5,
                                  n_y_ticks=3, n_time_ticks=5, show_time_axis=True, 
                                  time_axis_min=0.0, time_axis_max=5000)
        from tvb_multiscale.core.plot.correlations_plot import plot_correlations
        plot_correlations(spikes_res["spikes_correlation_coefficient"], plotter)
        
if spikes_res:
    print("Mean spike rates:")
    for pop in spikes_res["mean_rate"].coords["Population"]:
        for reg in spikes_res["mean_rate"].coords["Region"]:
            if not np.isnan(spikes_res["mean_rate"].loc[pop, reg]):
                print("%s - %s: %g" % (pop.values.item().split("_spikes")[0], reg.values.item(), 
                                       spikes_res["mean_rate"].loc[pop, reg].values.item()))