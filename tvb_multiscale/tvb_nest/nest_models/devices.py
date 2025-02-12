# -*- coding: utf-8 -*-

import os
from abc import ABCMeta
import glob

import numpy as np
from numpy.lib.recfunctions import rename_fields
import xarray as xr

from tvb_multiscale.core.spiking_models.devices import \
    Device, InputDevice, OutputDevice, SpikeRecorder, Multimeter, Voltmeter, SpikeMultimeter
from tvb_multiscale.core.utils.data_structures_utils import flatten_neurons_inds_in_DataArray

from tvb.basic.neotraits.api import List

from tvb.contrib.scripts.utils.data_structures_utils \
    import ensure_list, extract_integer_intervals, data_xarray_from_continuous_events
from tvb.contrib.scripts.utils.file_utils import truncate_ascii_file_after_header


# These classes wrap around NEST commands.


class NESTDevice(Device):
    __metaclass__ = ABCMeta

    """NESTDevice class to wrap around a NEST output (recording) or input (stimulating) device"""

    nest_instance = None
    _weight_attr = "weight"
    _delay_attr = "delay"
    _receptor_attr = "receptor"

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "nest_device")
        super(NESTDevice, self).__init__(device, *args, **kwargs)
        self.nest_instance = nest_instance

    def _assert_nest(self):
        if self.nest_instance is None:
            raise ValueError("No NEST instance associated to this %s of model %s!" %
                             (self.__class__.__name__, self.model))

    def _assert_device(self):
        """Method to assert that the node of the network is a device"""
        try:
            self.device.get("element_type")
        except:
            raise ValueError("Failed to Get device %s!" % str(self.device))

    @property
    def global_id(self):
        return self.device.get("global_id")

    @property
    def virtual_process_id(self):
        return self.device.get("vp")

    @property
    def spiking_simulator_module(self):
        return self.nest_instance

    @property
    def nest_model(self):
        return str(self.device.get("model"))

    def Set(self, values_dict):
        """Method to set attributes of the device
           Arguments:
            values_dict: dictionary of attributes names' and values.
        """
        self.device.set(values_dict)

    def Get(self, attrs=None):
        """Method to get attributes of the device.
           Arguments:
            attrs: names of attributes to be returned. Default = None, corresponds to all neurons' attributes.
           Returns:
            Dictionary of attributes.
        """
        if attrs is None:
            return self.device.get()
        else:
            return self.device.get(attrs)

    def _GetConnections(self, **kwargs):
        """Method to get attributes of the connections from/to the device
           Return:
            connections' objects
        """
        self._assert_nest()
        for kw in ["source", "target"]:
            kwval = kwargs.get(kw, None)
            if kwval is not None:
                if len(kwval) == 0:
                    kwval = None
                elif not isinstance(kwval, self.nest_instance.NodeCollection):
                    kwval = self.nest_instance.NodeCollection(kwval)
                kwargs[kw] = kwval
        connections = self.nest_instance.GetConnections(**kwargs)
        if len(connections) == 0:
            return ()
        else:
            return connections

    def _SetToConnections(self, values_dict, connections=None):
        """Method to set attributes of the connections from/to the device
            Arguments:
             values_dict: dictionary of attributes names' and values.
             connections: A SynapseCollection. Default = None, corresponding to all device's connections
            Returns:
             Dictionary of lists of connections' attributes.
        """
        if connections is None:
            connections = self._GetConnections()
        connections.set(values_dict)

    def _GetFromConnections(self, attrs=None, connections=None):
        """Method to get attributes of the connections from/to the device
           Arguments:
            attrs: collection (list, tuple, array) of the attributes to be included in the output.
                   Default = None, correspondingn to all devices' attributes
            connections: A SynapseCollection. Default = None, corresponding to all device's connections
           Returns:
            Dictionary of lists of connections' attributes.
        """
        if connections is None:
            connections = self._GetConnections()
        if attrs is None:
            return connections.get()
        else:
            return connections.get(ensure_list(attrs))

    def GetConnections(self):
        """Method to get all connections of the device from neurons.
           Returns:
            SynapseCollection.
        """
        return self._GetConnections(source=self.device)

    @property
    def connections(self):
        """Method to get all connections of the device from neurons.
           Returns:
            SynapseCollection..
        """
        return self._GetConnections(source=self.device)

    def get_neurons(self, source_or_target="target"):
        """Method to get the indices of all the neurons the device is connected from/to.
           Mind that for all input and all out output devices, except for spike detector,
           the devices connects to the neurons, and not vice-versa,
           i.e., neurons are the target of the device connection.
        """
        neurons = []
        for conn in self.connections:
            neuron = getattr(conn, source_or_target)
            if neuron is not None:
                neurons.append(neuron)
        return tuple(np.unique(neurons).tolist())

    @property
    def neurons(self):
        """Method to get the indices of all the neurons the device is connected to."""
        return self.get_neurons("target")

    def _print_neurons(self, neurons):
        return "%d neurons: %s" %(self.number_of_neurons, extract_integer_intervals(neurons, print=True))


class NESTInputDevice(NESTDevice, InputDevice):

    """NESTInputDevice class to wrap around a NEST input (stimulating) device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "nest_input_device")
        super(NESTInputDevice, self).__init__(device, nest_instance, *args, **kwargs)


class NESTPoissonGenerator(NESTInputDevice):

    """NESTPoissonGenerator class to wrap around a NEST poisson_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "poisson_generator")
        super(NESTPoissonGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTSinusoidalPoissonGenerator(NESTInputDevice):

    """NESTSinusoidalPoissonGenerator class to wrap around a NEST sinusoidal_poisson_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "sinusoidal_poisson_generator")
        super(NESTSinusoidalPoissonGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTInhomogeneousPoissonGenerator(NESTInputDevice):

    """NESTInhomogeneousPoissonGenerator class to wrap around a NEST inhomogeneous_poisson_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "inhomogeneous_poisson_generator")
        super(NESTInhomogeneousPoissonGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTMIPGenerator(NESTInputDevice):

    """NESTMIPGenerator class to wrap around a NEST mip_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "mip_generator")
        super(NESTMIPGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTGammaSupGenerator(NESTInputDevice):

    """NESTGammaSupGenerator class to wrap around a NEST gamma_sup_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "gamma_sup_generator")
        super(NESTGammaSupGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTDPPDSupGenerator(NESTInputDevice):

    """NESTDPPDSupGenerator class to wrap around a NEST ppd_sup_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "ppd_sup_generator")
        super(NESTDPPDSupGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTSpikeGenerator(NESTInputDevice):

    """NESTSpikeGenerator class to wrap around a NEST spike_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "spike_generator")
        super(NESTSpikeGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTPulsePacketGenerator(NESTInputDevice):

    """NESTPulsePacketGenerator class to wrap around a NEST pulse_packet_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "pulse_packet_generator")
        super(NESTPulsePacketGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTDCGenerator(NESTInputDevice):

    """NESTDCGenerator class to wrap around a NEST dc_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "dc_generator")
        super(NESTDCGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTStepCurrentGenerator(NESTInputDevice):

    """NESTStepCurrentGenerator class to wrap around a NEST step_current_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "step_current_generator")
        super(NESTStepCurrentGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTACGenerator(NESTInputDevice):

    """NESTACGenerator class to wrap around a NEST ac_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "ac_generator")
        super(NESTACGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTStepRateGenerator(NESTInputDevice):

    """NESTStepRateGenerator class to wrap around a NEST step_rate_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "step_rate_generator")
        super(NESTStepRateGenerator, self).__init__(device, nest_instance, *args, **kwargs)


class NESTNoiseGenerator(NESTInputDevice):

    """NESTNoiseGenerator class to wrap around a NEST noise_generator device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "noise_generator")
        super(NESTNoiseGenerator, self).__init__(device, nest_instance, *args, **kwargs)


NESTSpikeInputDeviceDict = {"poisson_generator": NESTPoissonGenerator,
                            "sinusoidal_poisson_generator": NESTSinusoidalPoissonGenerator,
                            "inhomogeneous_poisson_generator": NESTInhomogeneousPoissonGenerator,
                            "mip_generator": NESTMIPGenerator,
                            "gamma_sup_generator": NESTGammaSupGenerator,
                            "ppd_sup_generator": NESTDPPDSupGenerator,
                            "spike_generator": NESTSpikeGenerator,
                            "pulse_packet_generator": NESTPulsePacketGenerator
                            }


NESTCurrentInputDeviceDict = {"dc_generator": NESTDCGenerator,
                              "step_current_generator": NESTStepCurrentGenerator,
                              "ac_generator": NESTACGenerator,
                              "step_rate_generator": NESTStepRateGenerator,
                              "noise_generator": NESTNoiseGenerator
                              }


NESTInputDeviceDict = {}
NESTInputDeviceDict.update(NESTSpikeInputDeviceDict)
NESTInputDeviceDict.update(NESTCurrentInputDeviceDict)


def read_nest_output_device_data_from_ascii_to_dict(filepath):
    """This function reads data from a NEST recording device ascii file into an events dictionary
       Arguments:
        - filepath: absolute or relative path to the file (string)
       Returns:
        the events dictionary of the recorded data
    """
    recarray = rename_fields(np.genfromtxt(filepath, names=True, skip_header=2),
                             {"sender": "senders", "time_ms": "times"})
    return {name: ensure_list(recarray[name]) for name in recarray.dtype.names}


class NESTOutputDevice(NESTDevice, OutputDevice):

    """NESTOutputDevice class to wrap around a NEST output (recording) device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "nest_output_device")
        super(NESTOutputDevice, self).__init__(device, nest_instance, *args, **kwargs)
        if kwargs.get("record_to", "ascii") == "ascii":
            self._get_events = self._get_events_from_ascii
            self._reset = self._delete_events_in_ascii_files
        else:
            self._get_events = self._get_events_from_memory
            self._reset = self._delete_events_in_memory

    @property
    def record_from(self):
        return []

    def _get_filenames(self):
        return glob.glob(os.path.join(self.nest_instance.GetKernelStatus("data_path"), "%s*" % self.label))

    @property
    def _empty_events(self):
        keys = ["times", "senders"] + self.record_from
        return dict(zip(keys, [[]]*len(keys)))

    def _get_events_from_ascii(self):
        events = self._empty_events
        filenames = self._get_filenames()
        for filepath in filenames:
            this_file_events = read_nest_output_device_data_from_ascii_to_dict(filepath)
            for key in events.keys():
                events[key] = events[key] + this_file_events[key]
        return events

    def _get_events_from_memory(self):
        return self.device.get("events")

    @property
    def events(self):
        return self._get_events()

    @property
    def number_of_events(self):
        return self.device.get("n_events")

    @property
    def n_events(self):
        return self.number_of_events

    def _delete_events_in_ascii_files(self):
        for filepath in self._get_filenames():
            truncate_ascii_file_after_header(filepath, header_chars="#")

    def _delete_events_in_memory(self):
        # TODO: find how to reset recorders!
        pass
        # self.device.n_events = 0

    def reset(self):
        self._reset()


class NESTSpikeRecorder(NESTOutputDevice, SpikeRecorder):

    """NESTSpikeRecorder class to wrap around a NEST spike_recorder device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "spike_recorder")
        super(NESTSpikeRecorder, self).__init__(device, nest_instance, *args, **kwargs)

    # Only SpikeRecorder is the target of connections with neurons in NEST:

    def GetConnections(self):
        """Method to get connections of the device from neurons.
           Returns:
            connections' objects.
        """
        return self._GetConnections(target=self.device)

    @property
    def connections(self):
        """Method to get all connections of the device from neurons.
           Returns:
            connections' objects.
        """
        return self._GetConnections(target=self.device)

    @property
    def neurons(self):
        """Method to get the indices of all the neurons the device is connected to."""
        return self.get_neurons("source")


class NESTMultimeter(NESTOutputDevice, Multimeter):

    """NESTMultimeter class to wrap around a NEST multimeter device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "multimeter")
        super(NESTMultimeter, self).__init__(device, nest_instance, *args, **kwargs)

    @property
    def record_from(self):
        return [str(name) for name in self.device.get('record_from')]

    def get_data(self, variables=None, name=None, dims_names=["Time", "Variable", "Neuron"], flatten_neurons_inds=True):
        """This method returns time series' data recorded by the multimeter.
           Arguments:
            variables: a sequence of variables' names (strings) to be selected.
                       Default = None, corresponds to all variables the multimeter records from.
            name: label of output. Default = None, which defaults to the label of the Device
            dims_names: sequence of dimensions' labels (strings) for the output array.
                        Default = ["Time", "Variable", "Neuron"]
           Returns:
            a xarray DataArray with the output data
        """
        if name is None:
            name = self.label
        events = self.events
        times = events.pop("times")
        senders = events.pop("senders")
        if len(times) + len(senders):
            # We assume that the multimeter captures events even for continuous variables as it is the case in NEST.
            # Therefore, we have to re-arrange the output to get all variables separated following time order.
            data = data_xarray_from_continuous_events(events, times, senders,
                                                      variables=self._determine_variables(variables),
                                                      name=name, dims_names=dims_names)
            if flatten_neurons_inds:
                data = flatten_neurons_inds_in_DataArray(data, data.dims[2])
        else:
            vars = self._determine_variables(variables)
            data = xr.DataArray(np.empty((len(times), len(vars), len(senders))), name=name, dims=dims_names,
                                coords={dims_names[0]: times, dims_names[1]: vars, dims_names[2]: senders})
        return data
    
    
class NESTVoltmeter(NESTMultimeter, Voltmeter):

    """NESTVoltmeter class to wrap around a NEST voltmeter device"""

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "voltmeter")
        super(NESTVoltmeter, self).__init__(device, nest_instance, *args, **kwargs)
        assert self.var in self.record_from
        
    @property
    def var(self):
        return "V_m"
    
    @property
    def get_V_m(self):
        return self.var

    @property
    def V_m(self):
        return self.var
    
    
class NESTSpikeMultimeter(NESTMultimeter, NESTSpikeRecorder, SpikeMultimeter):

    """NESTSpikeMultimeter class to wrap around a NEST multimeter device
       that records only from continuous time spike weights variable."""

    spike_vars = List(of=str, default=["spikes"],
                      label="Spike variables' labels list",
                      doc="""List of labels of spike variables""")

    def __init__(self, device, nest_instance, *args, **kwargs):
        kwargs["model"] = kwargs.pop("model", "spike_multimeter")
        super(NESTSpikeMultimeter, self).__init__(device, nest_instance, *args, **kwargs)


NESTOutputSpikeDeviceDict = {"spike_recorder": NESTSpikeRecorder}


NESTOutputContinuousTimeDeviceDict = {"multimeter": NESTMultimeter,
                                      "spike_multimeter": NESTSpikeMultimeter,
                                      "voltmeter": NESTVoltmeter}


NESTOutputDeviceDict = {}
NESTOutputDeviceDict.update(NESTOutputSpikeDeviceDict)
NESTOutputDeviceDict.update(NESTOutputContinuousTimeDeviceDict)
