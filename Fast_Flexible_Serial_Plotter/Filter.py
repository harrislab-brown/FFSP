import numpy as np
from scipy import fft, signal
from numpy import mean, std



class Filter:
    def __init__(self, cutoff_freq, sample_rate, num_traces = 1):
        self.cutoff_freq = cutoff_freq
        self.sample_rate = sample_rate
        self.num_traces = num_traces

        self.nyquist_freq = self.sample_rate / 2

        #Wn = self.cutoff_freq / self.nyquist_freq
        self.filter_arg_b, self.filter_arg_a = signal.butter( 3, self.cutoff_freq, 'lowpass', fs = self.sample_rate)


    def apply_filter(self, data):
        # Applies the filter to data. Sets output_buff object variable to filtered data, which is used by later methods
        # apply filter to a different data frame to process next batch of data
        raw_data = np.asarray(data)
        filtered_data = signal.filtfilt(self.filter_arg_b, self.filter_arg_a, raw_data[:,0])
        return np.expand_dims(filtered_data, axis=1).tolist()
        

    def OLD_find_trig_index(self):
        cycle_list = []
        trigger_list = []
        accel_list = []
        trigger_index = 0
        #thresh = (max(self.output_buff[15:-15]) + min(self.output_buff[15:-15])) * 0.5
        thresh = (max(self.output_buff[:]) + min(self.output_buff[:])) * 0.5


        for i in range(1,len(self.output_buff)):
            if((self.output_buff[i-1] < thresh) and (self.output_buff[i] >= thresh)):
                cycle = self.output_buff[trigger_index:i-1]
                cycle_list.append(cycle)
                trigger_index = i
                trigger_list.append(i)
            
        for i in range(1,len(cycle_list)-1):
            a_max = max(cycle_list[i])
            a_min = min(cycle_list[i])
            accel_list.append((a_max - a_min)/2)
        if (len(accel_list) >0):
            return mean(accel_list),std(accel_list)
        else:
            return 0,0

    def find_thd(slef):
        pass