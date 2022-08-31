import numpy as np
import matplotlib.pyplot as plt

#m1 = np.genfromtxt('PSD_M1.csv', delimiter=',')
#s1 = np.genfromtxt('PSD_S1.csv', delimiter=',')


#with open('PSD_M1.npy', 'wb') as f:
#    np.save(f, m1)

#with open('PSD_S1.npy', 'wb') as f:
#    np.save(f, s1)


with open('PSD_M1.npy', 'rb') as f:
    m1 = np.load(f)

with open('PSD_S1.npy', 'rb') as f:
    s1 = np.load(f)

fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.plot(m1[:,0],m1[:,1],'b')
ax1.set_yscale('log')
ax1.set_ylim([0,1000])
ax1.set_ylabel('PSD')
ax1.set_xlabel('Frequency [Hz]')
ax1.set_title('M1')


ax2.plot(s1[:,0],s1[:,1],'r')
ax2.set_yscale('log')
ax2.set_ylim([0,1000])
ax2.set_xlabel('Frequency [Hz]')
ax2.set_title('S1')
plt.show()

print(m1)
