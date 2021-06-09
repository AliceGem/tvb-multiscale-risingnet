# -*- coding: utf-8 -*-

from logging import Logger
from abc import ABCMeta, ABC

import numpy as np

from tvb.basic.neotraits._attr import Attr
from tvb.contrib.scripts.utils.data_structures_utils import ensure_list
from tvb.contrib.cosimulation.cosim_monitors import RawCosim, CosimCoupling, CosimMonitorFromCoupling

from tvb_multiscale.core.config import Config, CONFIGURED, initialize_logger
from tvb_multiscale.core.interfaces.base.builder import InterfaceBuilder
from tvb_multiscale.core.interfaces.spikeNet.builders import \
    SpikeNetProxyNodesBuilder, DefaultTVBtoSpikeNetModels, DefaultSpikeNetToTVBModels
from tvb_multiscale.core.interfaces.base.io import RemoteSenders, RemoteReceivers
from tvb_multiscale.core.interfaces.base.transformers.builders import \
    TVBtoSpikeNetTransformerBuilder, SpikeNetToTVBTransformerBuilder
from tvb_multiscale.core.interfaces.tvb.interfaces import \
    TVBOutputInterfaces, TVBInputInterfaces, TVBOutputInterface, TVBInputInterface, \
    TVBSenderInterface, TVBReceiverInterface, TVBTransformerSenderInterface, TVBReceiverTransformerInterface, \
    TVBtoSpikeNetInterface, SpikeNetToTVBInterface, TVBtoSpikeNetInterfaces, SpikeNetToTVBInterfaces, \
    TVBtoSpikeNetModels, SpikeNetToTVBModels
from tvb_multiscale.core.tvb.cosimulator.cosimulator import CoSimulator


class TVBInterfaceBuilder(InterfaceBuilder):

    """TVBInterfaceBuilder abstract base class"""

    _output_interface_type = TVBOutputInterface
    _input_interface_type = TVBInputInterface

    _output_interfaces_type = TVBOutputInterfaces
    _input_interfaces_type = TVBInputInterfaces

    config = Attr(
        label="Configuration",
        field_type=Config,
        doc="""Configuration class instance.""",
        required=True,
        default=CONFIGURED
    )

    logger = Attr(
        label="Logger",
        field_type=Logger,
        doc="""logging.Logger instance.""",
        required=True,
        default=initialize_logger(__name__, config=CONFIGURED)
    )

    tvb_cosimulator = Attr(label="TVB simulator",
                           doc="""The instance of TVB simulator""",
                           field_type=CoSimulator,
                           required=True)

    exclusive_nodes = Attr(label="Flag of exclusive nodes",
                           doc="""Boolean flag that is true 
                                  if the co-simulator nodes are modelled exclusively by the co-simulator, 
                                  i.e., they are not simulated by TVB""",
                           field_type=bool,
                           default=True,
                           required=True)

    _default_out_proxy_inds = np.array([])
    _tvb_delays = None

    @property
    def tvb_dt(self):
        if self.tvb_cosimulator is None:
            return self.config.DEFAULT_DT
        return self.tvb_cosimulator.integrator.dt

    @property
    def synchronization_time(self):
        if self.tvb_cosimulator is None:
            return 0.0
        return self.tvb_cosimulator.synchronization_time

    @property
    def synchronization_n_step(self):
        if self.tvb_cosimulator is None:
            return 0
        return self.tvb_cosimulator.synchronization_n_step

    @property
    def tvb_nsig(self):
        try:
            return self.tvb_cosimulator.integrator.noise.nsig
        except:
            return np.array([0.0])

    @property
    def tvb_model(self):
        if self.tvb_cosimulator is None:
            return ""
        return self.tvb_cosimulator.model

    @property
    def tvb_model_state_variables(self):
        if self.tvb_cosimulator is None:
            return []
        return self.tvb_cosimulator.model.state_variables

    @property
    def tvb_model_cvar(self):
        if self.tvb_cosimulator is None:
            return []
        return self.tvb_cosimulator.model.cvar

    @property
    def number_of_regions(self):
        if self.tvb_cosimulator is None:
            return 0
        return self.tvb_cosimulator.connectivity.number_of_regions

    @property
    def region_labels(self):
        if self.tvb_cosimulator is None:
            return np.array([])
        return self.tvb_cosimulator.connectivity.region_labels

    @property
    def tvb_coupling_a(self):
        if self.tvb_cosimulator is None:
            return np.array([1.0/256])
        return self.tvb_cosimulator.coupling.a

    @property
    def tvb_weights(self):
        if self.tvb_cosimulator is None:
            return np.zeros((1, 1))
        return self.tvb_cosimulator.connectivity.weights

    def _get_tvb_delays(self):
        if self.tvb_cosimulator is None:
            idelays = np.ones((1, 1))
        else:
            idelays = self.tvb_cosimulator.connectivity.idelays
        return self.tvb_dt * idelays

    @property
    def tvb_delays(self):
        if self._tvb_delays is None:
            self._tvb_delays = self._get_tvb_delays()
        return self._tvb_delays

    def _proxy_inds(self, interfaces):
        return np.unique(self._only_inds_for_interfaces(interfaces, "proxy_inds", self.region_labels))

    @property
    def out_proxy_inds(self):
        return self._proxy_inds(self.output_interfaces)

    @property
    def in_proxy_inds(self):
        return self._proxy_inds(self.input_interfaces)

    def _voi_inds_labels_for_interface(self, interface):
        voi_inds = np.array(self._only_inds(interface["voi"], self.tvb_model_state_variables))
        voi_labels = np.array(self.tvb_model_state_variables)[voi_inds]
        return voi_inds, voi_labels

    def _voi_inds(self, interfaces):
        return np.unique(self._only_inds_for_interfaces(interfaces, "voi", self.tvb_model_state_variables))

    @property
    def out_voi_inds(self):
        return self._voi_inds(self.output_interfaces)

    @property
    def in_voi_inds(self):
        return self._voi_inds(self.input_interfaces)

    @property
    def number_of_out_voi(self):
        return len(self.out_voi_inds)

    @property
    def number_of_in_voi(self):
        return len(self.in_voi_inds)

    def region_label_to_ind(self, labels):
        return self._label_to_ind(labels, self.region_labels)

    @property
    def out_proxy_labels(self):
        return self.region_labels[self.out_proxy_inds]

    @property
    def in_proxy_labels(self):
        return self.region_labels[self.in_proxy_inds]

    def voi_label_to_ind(self, voi):
        return self._label_to_ind(voi, self.tvb_cosimulator.model.state_variables)

    @property
    def out_voi_labels(self):
        return self.tvb_model_state_variables[self.out_voi_inds]

    @property
    def in_voi_labels(self):
        return self.tvb_model_state_variables[self.in_voi_inds]

    def _configure_proxys_vois(self, interface, default_proxy_inds):
        interface["proxy_inds"] = np.array(
            self._only_inds(
                ensure_list(interface.pop("proxy_inds", interface.pop("proxy", default_proxy_inds))),
                self.region_labels))
        assert (interface["proxy_inds"] >= 0).all and (interface["proxy_inds"] <= self.number_of_regions).all
        voi_inds, voi_labels = self._voi_inds_labels_for_interface(interface)
        interface["voi"] = voi_inds
        interface["voi_labels"] = voi_labels

    def _configure_input_proxys_vois(self):
        for interface in self.input_interfaces:
            self._configure_proxys_vois(interface, interface.get("spiking_proxy_inds", self.proxy_inds))

    def _configure_output_proxys_vois(self):
        for interface in self.output_interfaces:
            if self.is_tvb_coupling_interface(interface):
                self._configure_proxys_vois(interface, interface.get("spiking_proxy_inds", self.proxy_inds))
            else:
                self._configure_proxys_vois(interface, self._default_out_proxy_inds)

    def _vois_to_monitor_mapping(self):
        raw_vois_to_monitor = {}
        coupl_vois_to_monitor = {}
        for iM, cosim_monitor in enumerate(self.tvb_cosimulator.cosim_monitors):
            if isinstance(cosim_monitor, CosimMonitorFromCoupling):
                coupl_vois_to_monitor[tuple(cosim_monitor.voi)] = iM
            else:
                raw_vois_to_monitor[tuple(cosim_monitor.voi)] = iM
        return raw_vois_to_monitor, coupl_vois_to_monitor

    def _create_cosim_monitor(self, interface, new_monitor, vois_to_monitor_mapping):
        # ...set the monitor_ind,
        interface["monitor_ind"] = len(self.tvb_cosimulator.cosim_monitors)
        # ...update the current mappings,
        vois_to_monitor_mapping[tuple(new_monitor.variables_of_interest)] = interface["monitor_ind"]
        # ...and finally add the monitor to the cosimulator:
        self.tvb_cosimulator.cosim_monitors += (new_monitor,)
        return vois_to_monitor_mapping

    def _configure_cosim_monitors(self):
        """This method will make sure that default RawCosim or CouplingCosim monitors
           are created if the user hasn't already defined them.
           It also sets the correct monitor_ind for each interface."""
        # Loop through the user defined interfaces
        # and make sure that all vois are being taken care by a suitable monitor
        for interface in self.output_interfaces:
            raw_vois_to_monitor, coupl_vois_to_monitor = self._vois_to_monitor_mapping()
            if self.is_tvb_coupling_interface(interface):  # check if it is a coupling interface
                # NOTE!!!: interface voi indices correspond to state variables indices,
                # whereas CosimCoupling monitors point to cvar indices!
                cvar = self.tvb_cosimulator.model.cvar.tolist()
                cvoi = [cvar.index(voi) for voi in interface["voi"]]
                if tuple(cvoi) not in list(coupl_vois_to_monitor.keys()):
                    # Assuming a CosimCoupling monitor ...create it:
                    coupl_vois_to_monitor = \
                        self._create_cosim_monitor(interface,
                                                   CosimCoupling(variables_of_interest=np.array(cvoi),
                                                                 period=self.tvb_dt),
                                                   coupl_vois_to_monitor)
                else:
                    interface["monitor_ind"] = coupl_vois_to_monitor[tuple(cvoi)]
            else:
                if tuple(interface["voi"]) not in list(raw_vois_to_monitor.keys()):
                    # # Assuming a RawCosim monitor create it,
                    raw_vois_to_monitor = \
                        self._create_cosim_monitor(interface,
                                                   RawCosim(variables_of_interest=np.array(interface["voi"]),
                                                            period=self.tvb_dt),
                                                   raw_vois_to_monitor)
                else:
                    interface["monitor_ind"] = raw_vois_to_monitor[tuple(interface["voi"])]

    def configure(self):
        super(TVBInterfaceBuilder, self).configure()
        self._default_out_proxy_inds = np.arange(self.number_of_regions).astype('i').tolist()
        self._configure_input_proxys_vois()
        if self.exclusive_nodes:
            for proxy_ind in self.in_proxy_inds:
                self._default_out_proxy_inds.remove(proxy_ind)
        self._default_out_proxy_inds = np.array(self._default_out_proxy_inds)
        self._configure_output_proxys_vois()
        self._configure_cosim_monitors()

    def _get_output_interface_arguments(self, interface):
        return interface

    def _get_input_interface_arguments(self, interface):
        return interface

    def build(self):
        self.build_interfaces()
        self.tvb_cosimulator.exclusive = self.exclusive_nodes
        self.tvb_cosimulator.output_interfaces = self._output_interfaces_type(interfaces=self._output_interfaces)
        self.tvb_cosimulator.input_interfaces = self._input_interfaces_type(interfaces=self._input_interfaces)
        return self.tvb_cosimulator


class TVBRemoteInterfaceBuilder(TVBInterfaceBuilder):

    """TVBRemoteInterfaceBuilder class"""

    _output_interface_type = TVBSenderInterface
    _input_interface_type = TVBReceiverInterface
    
    _remote_sender_types = [val.value for val in RemoteSenders.__members__.values()]
    _remote_receiver_types = [val.value for val in RemoteReceivers.__members__.values()]

    def configure(self):
        super(TVBRemoteInterfaceBuilder, self).configure()
        self._assert_output_interfaces_component_config(self._remote_sender_types, "sender")
        self._assert_input_interfaces_component_config(self._remote_receiver_types, "receiver")

    def _get_output_interface_arguments(self, interface):
        interface = super(TVBRemoteInterfaceBuilder, self)._get_output_interface_arguments(interface)
        interface["communicator"] = interface.pop("sender")
        return interface

    def _get_input_interface_arguments(self, interface):
        interface = super(TVBRemoteInterfaceBuilder, self)._get_input_interface_arguments(interface)
        interface["communicator"] = interface.pop("receiver")
        return interface


class TVBOutputTransformerInterfaceBuilder(TVBRemoteInterfaceBuilder, TVBtoSpikeNetTransformerBuilder):

    """TVBOutputTransformerInterfaceBuilder class"""

    _output_interface_type = TVBTransformerSenderInterface
    _input_interface_type = TVBReceiverInterface

    def configure(self):
        if self.dt == 0.0:
            # From TVBInterfaceBuilder to TransformerBuilder:
            self.dt = self.tvb_dt
        TVBRemoteInterfaceBuilder.configure(self)
        self.configure_and_build_transformer(self)

    def _get_output_interface_arguments(self, interface):
        interface.update(super(TVBOutputTransformerInterfaceBuilder, self)._get_output_interface_arguments(interface))
        return interface


class TVBInputTransformerInterfaceBuilder(TVBRemoteInterfaceBuilder, SpikeNetToTVBTransformerBuilder):

    """TVBInputTransformerInterfaceBuilder class"""

    _output_interface_type = TVBSenderInterface
    _input_interface_type = TVBReceiverTransformerInterface

    def configure(self):
        if self.dt == 0.0:
            # From TVBInterfaceBuilder to TransformerBuilder:
            self.dt = self.tvb_dt
        TVBRemoteInterfaceBuilder.configure(self)
        self.configure_and_build_transformer(self)

    def _get_input_interface_arguments(self, interface):
        interface = super(TVBInputTransformerInterfaceBuilder, self)._get_input_interface_arguments(interface)
        return interface


class TVBTransfomerInterfaceBuilder(TVBRemoteInterfaceBuilder,
                                    TVBtoSpikeNetTransformerBuilder, SpikeNetToTVBTransformerBuilder):

    """TVBTransfomerInterfaceBuilder class"""

    _output_interface_type = TVBTransformerSenderInterface
    _input_interface_type = TVBReceiverTransformerInterface

    def configure(self):
        if self.dt == 0.0:
            # From TVBInterfaceBuilder to TransformerBuilder:
            self.dt = self.tvb_dt
        TVBRemoteInterfaceBuilder.configure(self)
        TVBtoSpikeNetTransformerBuilder.configure_and_build_transformer(self, self.output_interfaces)
        SpikeNetToTVBTransformerBuilder.configure_and_build_transformer(self, self.input_interfaces)

    def _get_output_interface_arguments(self, interface):
        interface = super(TVBTransfomerInterfaceBuilder, self)._get_output_interface_arguments(interface)
        return interface

    def _get_input_interface_arguments(self, interface):
        interface = TVBTransfomerInterfaceBuilder._get_input_interface_arguments(self, interface)
        return interface


class TVBSpikeNetInterfaceBuilder(TVBInterfaceBuilder, SpikeNetProxyNodesBuilder,
                                  TVBtoSpikeNetTransformerBuilder, SpikeNetToTVBTransformerBuilder, ABC):
    __metaclass__ = ABCMeta

    """TVBSpikeNetInterfaceBuilder abstract base class"""

    _tvb_to_spikeNet_models = list(TVBtoSpikeNetModels.__members__)
    _spikeNet_to_tvb_models = list(SpikeNetToTVBModels.__members__)

    _default_nest_to_tvb_models = DefaultSpikeNetToTVBModels
    _default_tvb_to_nest_models = DefaultTVBtoSpikeNetModels

    _input_proxy_models = None   # Input to SpikeNet is output of TVB
    _output_proxy_models = None  # Output of SpikeNet is input to TVB

    _output_interfaces_type = TVBtoSpikeNetInterfaces
    _input_interfaces_type = SpikeNetToTVBInterfaces

    _output_interface_type = TVBtoSpikeNetInterface
    _input_interface_type = SpikeNetToTVBInterface

    @property
    def tvb_nodes_inds(self):
        return self._default_out_proxy_inds

    @property
    def spiking_nodes_inds(self):
        return self.in_proxy_inds

    def configure(self):
        if self.dt == 0.0:
            # From TVBInterfaceBuilder to
            # SpikeNetProxyNodesBuilder, TVBtoSpikeNetTransformerBuilder, SpikeNetToTVBTransformerBuilder:
            self.dt = self.tvb_dt
        TVBInterfaceBuilder.configure(self)
        SpikeNetProxyNodesBuilder.configure(self)
        self._configure_proxy_models(self.output_interfaces, self._tvb_to_spikeNet_models,
                                     self._default_tvb_to_nest_models, self._output_proxy_models)
        self._configure_proxy_models(self.input_interfaces, self._spikeNet_to_tvb_models,
                                     self._default_nest_to_tvb_models, self._input_proxy_models)
        TVBtoSpikeNetTransformerBuilder.configure_and_build_transformer(self, self.output_interfaces)
        SpikeNetToTVBTransformerBuilder.configure_and_build_transformer(self, self.input_interfaces)

    def _get_spikeNet_interface_arguments(self, interface):
        interface.update({"spiking_network": self.spiking_network, "populations": np.array(interface["populations"])})

    def _get_spikeNet_output_interface_arguments(self, interface):
        self._get_spikeNet_interface_arguments(interface)
        interface["dt"] = self.tvb_dt
        self._get_spiking_proxy_inds_for_output_interface(interface, self.exclusive_nodes)
        self._build_spikeNet_to_tvb_interface_proxy_nodes(interface)

    def _get_spikeNet_input_interface_arguments(self, interface):
        self._get_spikeNet_interface_arguments(interface)
        self._get_spiking_proxy_inds_for_input_interface(interface, self.exclusive_nodes)
        self._build_tvb_to_spikeNet_interface_proxy_nodes(interface)

    def _get_output_interface_arguments(self, interface):
        self._get_spikeNet_input_interface_arguments(
            TVBInterfaceBuilder._get_output_interface_arguments(self, interface))
        return interface

    def _get_input_interface_arguments(self, interface):
        self._get_spikeNet_output_interface_arguments(
            TVBInterfaceBuilder._get_input_interface_arguments(self, interface))
        return interface
