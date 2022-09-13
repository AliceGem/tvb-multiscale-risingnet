# Import packages
from audioop import avg
import pickle
import numpy as np
import os

from examples.tvb_nest.notebooks.cerebellum.scripts.scripts import *
from examples.tvb_nest.notebooks.cerebellum.utils import  compute_plot_selected_spectra_coherence, only_plot_selected_spectra_coherence_and_diff

LOAD_COHERENCE = False      # If coherence was already computed outside and loaded into file

test_names = ['MF_cerebON', 'MF_cerebOFF','cosim']

if LOAD_COHERENCE:
    # Load files
    avg_coherence = {}
    for test in test_names:
        file_coherence = open("coherence_"+test+"_2sec.pickle",'rb')
        print(file_coherence)
        [CxyR, fR, fL, CxyL]=pickle.load(file_coherence)
        avg_coherence[test] = np.mean(np.array([CxyR,CxyL]),axis=0)
else:       # compute coherence from time series
    # Get configuration
    config, plotter = configure()
    #config.SIMULATION_LENGTH = 2000.0
    plotter = None
    
    # Load connectome and other structural files
    connectome, major_structs_labels, voxel_count, inds = load_connectome(config, plotter=plotter)
    # Construct some more indices and maps
    inds, maps = construct_extra_inds_and_maps(connectome, inds)
    
    # Load time series
    relative_data_paths = {'MF_cerebON':'cwc_FIC_MFcerebON', 'MF_cerebOFF':'cwc_FIC_MFcerebOFF','cosim': 'cwc_FIC_MFcerebOFF'}
    
    avg_coherence = {}
    
    for test in test_names:
        file_ts = open(os.getcwd()+'/outputs/'+relative_data_paths[test]+'/res/source_ts.pkl','rb')
        print(file_ts)
        ts_object=pickle.load(file_ts)
        print(ts_object)
    
        #print("time series",ts_dict['time_series'].shape)
        
        

        # transient 4000
        NPERSEG = np.array([256, 512, 1024, 2048, 4096])
        NPERSEG = NPERSEG[np.argmin(np.abs(NPERSEG - (ts_object.shape[0]-4000/config.DEFAULT_DT)))]
        
        # Power Spectra and Coherence for M1 - S1 barrel field
        CxyR, fR, fL, CxyL = compute_plot_selected_spectra_coherence(ts_object, inds["m1s1brl"], 
                                                transient=4000, nperseg=NPERSEG, fmin=0.0, fmax=50.0)
        avg_coherence[test] = np.mean(np.array([CxyR,CxyL]),axis=0)
        
# Power Spectra and Coherence for M1 - S1 barrel field
color = {'cosim': 'black', 'MF_cerebON': 'gray', 'MF_cerebOFF': 'red'}
fig = only_plot_selected_spectra_coherence_and_diff(fR, avg_coherence, color, fmin=0.0, fmax=50.0, figsize=(15, 5))
fig.savefig('coherence_plot_comparison_test.png')
#fig.savefig('coherence_plot_comparison.svg')
