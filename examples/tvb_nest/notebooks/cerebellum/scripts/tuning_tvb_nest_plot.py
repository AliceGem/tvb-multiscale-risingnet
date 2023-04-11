# Import packages
from audioop import avg
import pickle
import numpy as np
import os, glob
import matplotlib.pyplot as plt

from examples.tvb_nest.notebooks.cerebellum.scripts.nest_utils import *
#from examples.tvb_nest.notebooks.cerebellum.scripts.scripts import *
from examples.tvb_nest.notebooks.cerebellum.utils import  compute_plot_selected_spectra_coherence, only_plot_selected_spectra_coherence_and_diff


cells = ['golgi']   #, 'granule', 'purkinje', 'basket', 'stellate', 'dcn', 'dcn_gaba', 'io', 'glom', 'mossy']
half = ['right', 'left']

SIM_DURATION = 1000
TRANSIENT = 500
# Load files
avg_frequency = {}
path_nest = 'outputs/0.1_/res/nest_recordings/'
path = 'outputs/0.1_/'

os.chdir(path_nest)
list_files = glob.glob("*.dat")

print(list_files)
nc = 0
for cell in cells:
    nh = 0
    avg_frequency[cells[nc]] = []
    for h in half: 
        print(cell, nh, nc)
        spikes = np.loadtxt(os.getcwd()+"/"+list_files[nc+nh],skiprows=3)
        # to use Denis functions (call Denis 11/01/2023): # nest_network.output_devices['E']['bankssts_L'].number_of_neurons
                                # nest_network.output_devices['E']['bankssts_L'].spikes_times
        current_frequency = compute_frequency_signal(spikes, duration=SIM_DURATION, cutoff=0)
        img=plt.plot(current_frequency)
        plt.title("Full signal "+h+" "+cell)
        plt.show()
        plt.savefig(h+'.png')
        img.write_image(h+'.png')
        current_frequency = compute_frequency_signal(spikes, duration=SIM_DURATION, cutoff=TRANSIENT)
        plt.title("Removed transient "+h+" "+cell)
        plt.plot(current_frequency)
        #plt.show()
        plt.savefig('rem_transient_fig.png')
        avg_frequency[cells[nc]].append(np.mean(current_frequency))
        nh+=1
    nc+=1

#print(avg_frequency['mossy'])   

# NEST to TVB
regs = [['Right Ansiform lobule', 'Left Ansiform lobule'],
            ['Right Interposed nucleus', 'Left Interposed nucleus'],
            ['Right Inferior olivary complex', 'Left Inferior olivary complex']]


import pickle
#pickle.load(path+'tvb_serial_cosimulator.pickle')
