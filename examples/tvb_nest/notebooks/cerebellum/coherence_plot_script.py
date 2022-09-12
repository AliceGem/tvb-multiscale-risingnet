# Import packages
import pickle
import numpy as np


from examples.tvb_nest.notebooks.cerebellum.utils import  only_plot_selected_spectra_coherence_and_diff


# Load files
test_names = ['MF_cerebON', 'MF_cerebOFF','cosim']

avg_coherence = {}
for test in test_names:
    file_coherence = open("coherence_"+test+"_2sec.pickle",'rb')
    print(file_coherence)
    [CxyR, fR, fL, CxyL]=pickle.load(file_coherence)
    avg_coherence[test] = np.mean(np.array([CxyR,CxyL]),axis=0)

# Power Spectra and Coherence for M1 - S1 barrel field
color = {'cosim': 'red', 'MF_cerebON': 'gray', 'MF_cerebOFF': 'black'}
fig = only_plot_selected_spectra_coherence_and_diff(fR, avg_coherence, color, fmin=0.0, fmax=50.0, figsize=(15, 5))
fig.savefig('coherence_plot_comparison.png')
fig.savefig('coherence_plot_comparison.svg')
