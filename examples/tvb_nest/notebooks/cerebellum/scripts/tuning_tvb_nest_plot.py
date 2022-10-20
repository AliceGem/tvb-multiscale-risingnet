# Import packages
from audioop import avg
import pickle
import numpy as np
import os, glob
import matplotlib.pyplot as plt

from examples.tvb_nest.notebooks.cerebellum.scripts.nest_utils import *
from examples.tvb_nest.notebooks.cerebellum.scripts.scripts import *
from examples.tvb_nest.notebooks.cerebellum.utils import  compute_plot_selected_spectra_coherence, only_plot_selected_spectra_coherence_and_diff


cells = ['golgi', 'granule', 'purkinje', 'basket', 'stellate', 'dcn', 'dcn_gaba', 'io', 'glom', 'mossy']
half = ['right', 'left']
# Load files
avg_frequency = {}
path = 'outputs/100__FIC/res/nest_recordings/'

os.chdir(path)
list_files = glob.glob("*.dat")

print(list_files)
nc = 0
for cell in cells:
    nh = 0
    avg_frequency[cells[nc]] = []
    for h in half: 
        print(cell, nh, nc)
        spikes = np.loadtxt(os.getcwd()+"/"+list_files[nc+nh],skiprows=3)
        current_frequency = compute_frequency_signal(spikes, duration=10000, cutoff=0)
        plt.plot(current_frequency)
        plt.title("Full signal "+h+" "+cell)
        plt.show()
        current_frequency = compute_frequency_signal(spikes, duration=10000, cutoff=8000)
        plt.title("Removed transient "+h+" "+cell)
        plt.plot(current_frequency)
        plt.show()
        avg_frequency[cells[nc]].append(np.mean(current_frequency))
        nh+=1
    nc+=1

print(avg_frequency['mossy'])
