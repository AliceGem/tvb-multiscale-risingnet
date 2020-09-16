# -*- coding: utf-8 -*-
from collections import OrderedDict

import numpy as np

from tvb_multiscale.core.spiking_models.population import SpikingPopulation

from tvb.contrib.scripts.utils.data_structures_utils import ensure_list, list_of_dicts_to_dicts_of_ndarrays


class ANNarchyPopulation(SpikingPopulation):

    annarchy_instance = None
    population_neurons = None
    _weight_attr = "weight"
    _delay_attr = "delay"
    _receptor_attr = "receptor"

    def __init__(self, population_neurons, label="", model="", annarchy_instance=None, **kwargs):
        self.annarchy_instance = annarchy_instance
        self.population_neurons = population_neurons
        super(ANNarchyPopulation, self).__init__(label, model, **kwargs)

    @property
    def spiking_simulator_module(self):
        return self.population_neurons

    @property
    def neurons(self):  # tuple of populations' neurons
        """Method to get all neurons' indices of this population.
           Returns:
            tuple of neurons'indices.
        """
        return tuple(self.node_collection.tolist())

    def _assert_nest(self):
        if self.nest_instance is None:
            raise ValueError("No NEST instance associated to this %s of model %s with label %s!" %
                             (self.__class__.__name__, self.model, self.label))

    def _print_neurons(self):
        return "\n%s" % str(self.node_collection)

    def _Set(self, neurons, values_dict):
        """Method to set attributes of the SpikingPopulation's neurons.
        Arguments:
            neurons: tuple of neurons the attributes of which should be set.
            values_dict: dictionary of attributes names' and values.
        """
        self._assert_nest()
        self.nest_instance.NodeCollection(neurons).set(values_dict)

    def _Get(self, neurons, attrs=None):
        """Method to get attributes of the SpikingPopulation's neurons.
           Arguments:
            neurons: tuple of neurons which should be included in the output.
            attrs: collection (list, tuple, array) of the attributes to be included in the output.
           Returns:
            Dictionary of lists of neurons' attributes.
        """
        self._assert_nest()
        if attrs is None:
            return self.nest_instance.NodeCollection(neurons).get()
        else:
            return self.nest_instance.NodeCollection(neurons).get(ensure_list(attrs))

    def _GetConnections(self, neurons=None, source_or_target=None):
        """Method to get all the connections from/to a SpikingPopulation neuron.
        Arguments:
            neurons: tuple of neurons the connections of which should be included in the output.
            source_or_target: Direction of connections relative to the populations' neurons
                              "source", "target" or None (Default; corresponds to both source and target)
           Returns:
            synapses' collections.
        """
        self._assert_nest()
        if neurons is not None:
            if len(neurons) == 0:
                neurons = None
        else:
            neurons = self.node_collection
        if neurons is not None and not isinstance(neurons, self.nest_instance.NodeCollection):
            neurons = self.nest_instance.NodeCollection(neurons)
        if source_or_target not in ["source", "target"]:
            return self.nest_instance.GetConnections(source=neurons), \
                   self.nest_instance.GetConnections(target=neurons)
        else:
            kwargs = {source_or_target: neurons}
            return self.nest_instance.GetConnections(**kwargs)

    def _SetToConnections(self, connections, values_dict):
        """Method to set attributes of the connections from/to the SpikingPopulation's neurons.
           Arguments:
             connections: connections' objects.
             values_dict: dictionary of attributes names' and values.
        """
        self._assert_nest()
        connections.set(values_dict)

    def _GetFromConnections(self, connections, attrs=None):
        """Method to get attributes of the connections from/to the SpikingPopulation's neurons.
            Arguments:
             connections: connections' objects.
            attrs: collection (list, tuple, array) of the attributes to be included in the output.
            Returns:
             Dictionary of arrays of connections' attributes.

        """
        self._assert_nest()
        if attrs is None:
            return connections.get()
        else:
            return connections.get(attrs)