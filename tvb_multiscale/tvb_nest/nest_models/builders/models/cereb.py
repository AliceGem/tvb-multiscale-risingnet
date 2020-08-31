# -*- coding: utf-8 -*-
import h5py

from collections import OrderedDict

import numpy as np

from tvb_multiscale.tvb_nest.config import CONFIGURED
from tvb_multiscale.tvb_nest.nest_models.builders.base import NESTModelBuilder


class CerebBuilder(NESTModelBuilder):

    path_to_network_source_file = ""

    # Synapse parameters: in E-GLIF, 3 synaptic receptors are present:
    # the first is always associated to exc,
    # the second to inh,
    # the third to remaining synapse type
    Erev_exc = 0.0  # [mV]	# [Cavallari et al, 2014]
    Erev_inh = -80.0  # [mV]
    # tau_exc for pc is for pf input; tau_exc for goc is for mf input; tau_exc for mli is for pf input:
    tau_exc = {'golgi': 0.23, 'granule': 5.8, 'purkinje': 1.1, 'basket': 0.64, 'stellate': 0.64, 'dcn': 1.0,
               'dcnp': 3.64,
               'io': 1.0}
    tau_inh = {'golgi': 10.0, 'granule': 13.61, 'purkinje': 2.8, 'basket': 2.0, 'stellate': 2.0, 'dcn': 0.7,
               'dcnp': 1.14, 'io': 60.0}
    tau_exc_cfpc = 0.4
    tau_exc_pfgoc = 0.5
    tau_exc_cfmli = 1.2

    # Single neuron parameters:
    neuron_param = {
        'golgi_cell': {'t_ref': 2.0, 'C_m': 145.0, 'tau_m': 44.0, 'V_th': -55.0, 'V_reset': -75.0, 'Vinit': -62.0,
                       'E_L': -62.0, 'Vmin': -150.0,
                       'lambda_0': 1.0, 'tau_V': 0.4, 'I_e': 16.214, 'kadap': 0.217, 'k1': 0.031, 'k2': 0.023,
                       'A1': 259.988, 'A2': 178.01,
                       'E_rev1': Erev_exc, 'E_rev2': Erev_inh, 'E_rev3': Erev_exc, 'tau_syn1': tau_exc['golgi'],
                       'tau_syn2': tau_inh['golgi'], 'tau_syn3': tau_exc_pfgoc},
        'granule_cell': {'t_ref': 1.5, 'C_m': 7.0, 'tau_m': 24.15, 'V_th': -41.0, 'V_reset': -70.0, 'Vinit': -62.0,
                         'E_L': -62.0, 'Vmin': -150.0,
                         'lambda_0': 1.0, 'tau_V': 0.3, 'I_e': -0.888, 'kadap': 0.022, 'k1': 0.311, 'k2': 0.041,
                         'A1': 0.01, 'A2': -0.94,
                         'E_rev1': Erev_exc, 'E_rev2': Erev_inh, 'E_rev3': Erev_exc, 'tau_syn1': tau_exc['granule'],
                         'tau_syn2': tau_inh['granule'], 'tau_syn3': tau_exc['granule']},
        'purkinje_cell': {'t_ref': 0.5, 'C_m': 334.0, 'tau_m': 47.0, 'V_th': -43.0, 'V_reset': -69.0, 'Vinit': -59.0,
                          'E_L': -59.0,
                          'lambda_0': 4.0, 'tau_V': 3.5, 'I_e': 742.54, 'kadap': 1.492, 'k1': 0.1950, 'k2': 0.041,
                          'A1': 157.622, 'A2': 172.622,
                          'E_rev1': Erev_exc, 'E_rev2': Erev_inh, 'E_rev3': Erev_exc, 'tau_syn1': tau_exc['purkinje'],
                          'tau_syn2': tau_inh['purkinje'], 'tau_syn3': tau_exc_cfpc},
        'basket_cell': {'t_ref': 1.59, 'C_m': 14.6, 'tau_m': 9.125, 'V_th': -53.0, 'V_reset': -78.0, 'Vinit': -68.0,
                        'E_L': -68.0,
                        'lambda_0': 1.8, 'tau_V': 1.1, 'I_e': 3.711, 'kadap': 2.025, 'k1': 1.887, 'k2': 1.096,
                        'A1': 5.953, 'A2': 5.863,
                        'E_rev1': Erev_exc, 'E_rev2': Erev_inh, 'E_rev3': Erev_exc, 'tau_syn1': tau_exc['basket'],
                        'tau_syn2': tau_inh['basket'], 'tau_syn3': tau_exc_cfmli},
        'stellate_cell': {'t_ref': 1.59, 'C_m': 14.6, 'tau_m': 9.125, 'V_th': -53.0, 'V_reset': -78.0, 'Vinit': -68.0,
                          'E_L': -68.0,
                          'lambda_0': 1.8, 'tau_V': 1.1, 'I_e': 3.711, 'kadap': 2.025, 'k1': 1.887, 'k2': 1.096,
                          'A1': 5.953, 'A2': 5.863,
                          'E_rev1': Erev_exc, 'E_rev2': Erev_inh, 'E_rev3': Erev_exc, 'tau_syn1': tau_exc['basket'],
                          'tau_syn2': tau_inh['basket'], 'tau_syn3': tau_exc_cfmli}}

    # Connection weights
    conn_weights = {'mossy_to_glomerulus': 1.0, 'ascending_axon_to_golgi': 0.05, 'ascending_axon_to_purkinje': 0.175,
                    'basket_to_purkinje': 3.638,
                    'glomerulus_to_golgi': 0.0125, 'glomerulus_to_granule': 0.361, 'golgi_to_granule': 0.338,
                    'parallel_fiber_to_basket': 0.002, 'parallel_fiber_to_golgi': 0.008,
                    'parallel_fiber_to_purkinje': 0.044,
                    'parallel_fiber_to_stellate': 0.003, 'stellate_to_purkinje': 1.213}

    # Connection delays
    conn_delays = {'mossy_to_glomerulus': 1.0, 'ascending_axon_to_golgi': 2.0, 'ascending_axon_to_purkinje': 2.0,
                   'basket_to_purkinje': 4.0,
                   'glomerulus_to_golgi': 4.0, 'glomerulus_to_granule': 4.0, 'golgi_to_granule': 2.0,
                   'parallel_fiber_to_basket': 5.0, 'parallel_fiber_to_golgi': 5.0, 'parallel_fiber_to_purkinje': 5.0,
                   'parallel_fiber_to_stellate': 5.0, 'stellate_to_purkinje': 5.0}

    # Connection receptors
    conn_receptors = {'ascending_axon_to_golgi': 3, 'ascending_axon_to_purkinje': 1, 'basket_to_purkinje': 2,
                      'glomerulus_to_golgi': 1, 'glomerulus_to_granule': 1, 'golgi_to_granule': 2,
                      'parallel_fiber_to_basket': 1, 'parallel_fiber_to_golgi': 3, 'parallel_fiber_to_purkinje': 1,
                      'parallel_fiber_to_stellate': 1, 'stellate_to_purkinje': 2}

    # Connection pre and post-synaptic neurons
    conn_pre_post = {'mossy_to_glomerulus': {'pre': 'mossy_fibers', 'post': 'glomerulus'},
                     'ascending_axon_to_golgi': {'pre': 'granule_cell', 'post': 'golgi_cell'},
                     'ascending_axon_to_purkinje': {'pre': 'granule_cell', 'post': 'purkinje_cell'},
                     'basket_to_purkinje': {'pre': 'basket_cell', 'post': 'purkinje_cell'},
                     'glomerulus_to_golgi': {'pre': 'glomerulus', 'post': 'golgi_cell'},
                     'glomerulus_to_granule': {'pre': 'glomerulus', 'post': 'granule_cell'},
                     'golgi_to_granule': {'pre': 'golgi_cell', 'post': 'granule_cell'},
                     'parallel_fiber_to_basket': {'pre': 'granule_cell', 'post': 'basket_cell'},
                     'parallel_fiber_to_golgi': {'pre': 'granule_cell', 'post': 'golgi_cell'},
                     'parallel_fiber_to_purkinje': {'pre': 'granule_cell', 'post': 'purkinje_cell'},
                     'parallel_fiber_to_stellate': {'pre': 'granule_cell', 'post': 'stellate_cell'},
                     'stellate_to_purkinje': {'pre': 'stellate_cell', 'post': 'purkinje_cell'}}

    RECORD_VM = False
    TOT_DURATION = 300.  # mseconds
    STIM_START = 100.  # beginning of stimulation
    STIM_END = 200.  # end of stimulation
    STIM_FREQ = 100.  # Frequency in Hz
    BACKGROUND_FREQ = 4.

    neuron_types = []
    start_id_scaffold = []

    def __init__(self, tvb_simulator, nest_nodes_ids, path_to_network_source_file,
                 nest_instance=None, config=CONFIGURED, set_defaults=True):
        super(CerebBuilder, self).__init__(tvb_simulator, nest_nodes_ids, nest_instance, config)
        self.path_to_network_source_file = path_to_network_source_file
        # Common order of neurons' number per population:
        self.population_order = 1  # we want scale to define exactly the number of neurons of each population
        self.modules_to_install = ["cereb"]
        if set_defaults:
            self.set_defaults()

    def set_populations(self):
        # Populations' configurations
        self.neuron_types = list(self.net_src_file['cells/placement'].keys())
        self.populations = []
        self.start_id_scaffold = {}
        self.pop_ids = {}
        # All cells are modelled as E-GLIF models;
        # with the only exception of Glomeruli and Mossy Fibers (not cells, just modeled as
        # relays; i.e., parrot neurons)
        for neuron_name in self.neuron_types:
            if neuron_name != 'glomerulus' and neuron_name != 'mossy_fibers':
                model = 'eglif_cond_alpha_multisyn'
            else:
                model = 'parrot_neuron'
            n_neurons = np.array(self.net_src_file['cells/placement/' + neuron_name + '/identifiers'])[1]
            self.populations.append(
                {"label": neuron_name, "model": model,
                 "params": self.neuron_param.get(neuron_name, {}),
                 "scale": n_neurons,
                 "nodes": None})
            self.start_id_scaffold[neuron_name] = \
                np.array(self.net_src_file['cells/placement/' + neuron_name + '/identifiers'])[0]

    def set_populations_connections(self):
        self.default_populations_connection["conn_spec"]["rule"] = "one_to_one"
        self.populations_connections = []
        for conn_name in self.conn_weights.keys():
            conn = np.array(self.net_src_file['cells/connections/'+conn_name])
            pre_name = self.conn_pre_post[conn_name]["pre"]
            post_name = self.conn_pre_post[conn_name]["post"]
            pre_fun = lambda neurons_inds: [int(x-self.start_id_scaffold[pre_name]+neurons_inds[0])
                                            for x in conn[:, 0].flatten()]
            post_fun = lambda neurons_inds: [int(x-self.start_id_scaffold[post_name]+neurons_inds[0])
                                             for x in conn[:, 1].flatten()]
            self.populations_connections.append(
                {"source": pre_name, "target": post_name,
                 "source_inds": pre_fun, "target_inds": post_fun,
                 "model": 'static_synapse',
                 "conn_spec": self.default_populations_connection["conn_spec"],
                 "weight": self.conn_weights[conn_name],
                 "delay": self.conn_delays[conn_name],
                 "receptor_type": self.conn_receptors.get(conn_name, 0),
                 "nodes": None
                 }
            )

    def set_spike_detector(self):
        connections = OrderedDict()
        #          label <- target population
        for pop in self.populations:
            connections[pop["label"] + "_spikes"] = pop["label"]
        params = dict(self.config.NEST_OUTPUT_DEVICES_PARAMS_DEF["spike_detector"])
        device = {"model": "spike_detector", "params": params,
                  "connections": connections, "nodes": None}  # None means all here
        return device

    def set_multimeter(self):
        connections = OrderedDict()
        #               label    <- target population
        for pop in self.populations:
            if pop["label"] != 'glomerulus' and pop["label"] != 'mossy_fibers':
                connections[pop["label"]] = pop["label"]
        params = dict(self.config.NEST_OUTPUT_DEVICES_PARAMS_DEF["multimeter"])
        params["interval"] = self.monitor_period
        device = {"model": "multimeter", "params": params,
                  "connections": connections, "nodes": None}  # None means all here
        return device

    def set_output_devices(self):
        # Creating  devices to be able to observe NEST activity:
        # Labels have to be different
        self.output_devices = [self.set_spike_detector(), self.set_multimeter()]

    def set_spike_stimulus(self):
        connections = OrderedDict()
        #             label <- target population
        connections["Stimulus"] = ['glomerulus']
        device = \
            {"model": "poisson_generator",
             "params": {"rate": self.STIM_FREQ, "origin": 0.0, "start": self.STIM_START, "stop": self.STIM_END},
             "connections": connections, "nodes": None,
             "weights": 1.0,
             "delays": 0.0,
             "receptor_type": 0}
        return device

    def set_spike_stimulus_background(self):
        connections = OrderedDict()
        #             label <- target population
        connections["Background"] = ['glomerulus']
        device = \
            {"model": "poisson_generator",
             "params": {"rate": self.BACKGROUND_FREQ, "origin": 0.0, "start": 0.0}, # not necessary: "stop": self.TOT_DURATION
             "connections": connections, "nodes": None,
             "weights": 1.0,
             "delays": 0.0,
             "receptor_type": 0}
        return device

    def set_input_devices(self):
        self.input_devices = [self.set_spike_stimulus(), self.set_spike_stimulus_background()]

    def set_defaults(self):
        self.net_src_file = h5py.File(self.path_to_network_source_file, 'r+')
        self.set_populations()
        self.set_populations_connections()
        self.set_output_devices()
        self.set_input_devices()
        self.net_src_file.close()