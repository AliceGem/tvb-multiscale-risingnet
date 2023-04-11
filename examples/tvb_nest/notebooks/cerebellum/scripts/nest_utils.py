# -*- coding: utf-8 -*-

import numpy as np


def compute_frequency_signal(spks, duration, cutoff=0, bin_dur=5):

   ind = spks[:,1]>cutoff
   spk_times = spks[ind,1]
   num_bin = int((duration-cutoff)/bin_dur)
   hist, bin_edges = np.histogram(spk_times, bins=num_bin)
   # Number of cells = number of cells firing
   cell_num = len(np.unique(spks[:,0]))
   frequency = hist/((bin_dur*0.001)*cell_num)
   print(frequency, frequency.shape)
   return frequency, num_bin


def compute_frequency_value(spks, duration, cutoff=0):

   ind = spks[:,1]>cutoff
   spk_times = spks[ind,1]
   
   # Number of cells = number of cells firing
   cell_num = len(np.unique(spks[:,0]))
   frequency = len(spk_times)/((duration-cutoff)*0.001*cell_num)
   print("cell_num", cell_num)
   return frequency
