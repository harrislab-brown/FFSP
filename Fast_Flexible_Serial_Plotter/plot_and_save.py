import numpy as np
import pygame
from datetime import datetime
from SerialMonitor import SerialMonitor
from Filter import Filter
from time import sleep

###
# Keyboard commands can be used to change plot parameters while program is running:
#   - s: pauses plot, prompts user to input a new sample rate in Hz (samples per second)
#   - b: pauses plot, prompts user to enter a new timebase in seconds (seconds division)
#   - t: changes plot behavior to use rising edge trigger or continuous scrolling data
###

class Animate:

    def __init__(self) -> None:

        # initialize the serial monitor
        # this starts the background thread to read the data
        # it also contains the data in a queue
        self.serial_monitor = SerialMonitor()
        self.data_chunk_size = 5000  # write to file every time we have this many data points

        self.debug_mode = False

        # setup pygame window:
        pygame.init()
        self.fps = 30
        self.width, self.height = 800, 400
        self.padding = 20
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont('Arial', 16)
        self.red = '0xab250e'
        self.red_trig = '0xd46450'
        self.grn = '0x1aab40'
        self.grn_trig = '0x8ce6a4'
        self.blu = '0x6f46db'
        self.channel_color = [self.red, self.grn, self.blu]
        self.grid_color = '0x727575'
        self.text_color = '0xEEEEEE'

        # plotting parameters:
        self.sample_rate = 10_000 #sample rate in Hz. 10kHz is default for microcontroller on boot
        self.cutoff_freq = self.sample_rate /2 -.01
        self.time_base = .01 # seconds to display on the screen at a time (horizontal scale)
        #self.y_scale = self.height / 1023
        self.y_scale = self.height / 5
        #self.y_offset = 0
        self.y_offset = self.height/2
        self.plot_grid = True
        self.plot_text = True
        self.use_triggering = False
        self.plot_filtered = False
        self.pause_plot = False
        self.set_plot_timing(self.sample_rate)

        # axis calibration parameters:
        x1 = 1440 # 1 g measurement 
        xn1 = -785 # -1 g measurement 
        y1 = 1430
        yn1 = -790
        z1 = 1550
        zn1 = -640

        x_zero = (x1 + xn1)/2
        x_sensitivity = x1 - x_zero
    
        y_zero = (y1 + yn1)/2
        y_sensitivity = y1 - y_zero

        z_zero = (z1 + zn1)/2
        z_sensitivity = z1 - z_zero
        self.axis_zero = [x_zero, y_zero, z_zero]
        self.axis_sensitivity = [x_sensitivity, y_sensitivity, z_sensitivity]

        self.save_file = False
        self.save_g_data = True # save raw data from accelerometer -> False, convert to G before saving -> True

        # begin animation loop:
        self.run_loop()

    def draw_background(self):
        # fill screen to cover last frame
        self.screen.fill('0x313837')

        # plot grid:
        num_vert_lines = 10
        num_hori_lines = 5

        if self.plot_grid:   
            for i in range(num_vert_lines+1): 
                y_val = i * self.height/num_vert_lines
                pygame.draw.line(self.screen,self.grid_color,(0,y_val),(self.width,y_val ))
            for i in range(num_hori_lines+1):
                x_val = i * (self.width-2*self.padding)/num_hori_lines
                pygame.draw.line(self.screen,self.grid_color,(x_val+self.padding,0),(x_val+self.padding,self.height))
            pygame.draw.line(self.screen,self.grid_color, (0,self.height/2),(self.width, self.height/2), 2 )

        # plot text:
        if self.plot_text:
            time_base_text = self.font.render("time base: " + str(self.time_base), True, self.text_color)
            sample_rate_text = self.font.render("sample rate: " + str(self.sample_rate), True, self.text_color)
            filter_cutoff_text = self.font.render("cutoff frequency: " + str(round(self.cutoff_freq)), True, self.text_color)
            hotkeys_text = self.font.render("hotkeys:   [ space  s  b  t  f  c ]", True, self.text_color)

            self.screen.blit(time_base_text, time_base_text.get_rect( x = 30, centery = self.height-self.padding))
            self.screen.blit(sample_rate_text, sample_rate_text.get_rect( x = 30 + (self.width-2*self.padding)/num_hori_lines , centery = self.height-self.padding))
            self.screen.blit(hotkeys_text, hotkeys_text.get_rect(x = 30, centery = self.height -self.padding - 40))
            if self.plot_filtered:
                self.screen.blit(filter_cutoff_text, filter_cutoff_text.get_rect( x = 30 + 3*(self.width-2*self.padding)/num_hori_lines , centery = self.height-self.padding))

    def end_animation(self):
        self.serial_monitor.close()
        if self.save_file:
            self.file.close()

    def set_plot_timing(self, new_sample_rate = 0):
        # sample rate argument: Specify a sample rate in Hz. If zero or no value is provided, sample rate will
        # remain the same. Otherwise, sample rate will be updated to the supplied argument. 

        # set sample rate and send new value to microcontroller:
        if new_sample_rate:
            sample_period_us = 1_000_000/(new_sample_rate) #microseconds per sample
            self.serial_monitor.serial_write(sample_period_us)
            self.sample_rate = new_sample_rate
            self.cutoff_freq = self.sample_rate/2 -.01


        self.plot_len = int(self.sample_rate * self.time_base * 5) # multiply by 5, which is the number of divisions in time
        self.plot_len_visible = self.plot_len

        # when using a rising edge trigger, we save twice as much data and only plot the data
        # in the region data[trig_index: trig_index + plot_len_visible]
        if self.use_triggering:
            self.plot_len = self.plot_len * 2 

        # create regularly spaced x axis array:
        self.time_range = np.linspace(self.padding, self.width - self.padding, num=self.plot_len_visible)

        # create digital lowpass filter with cutoff frequency set to nyquist frequency (sample rate/2)
        self.filter = Filter(self.cutoff_freq, self.sample_rate, self.plot_len)

    def find_trig_index(self, data, channel, thresh):

        trig_index = 0
        for i in range(1, len(data)):
            if((data[i-1][channel] < thresh) and (data[i][channel] >= thresh)):
                trig_index = i
        
        return trig_index # returns index of rising edge, or zero if no rising edge is found

    def toggle_save_data(self):
        # open output data file:
        if self.save_file == True:
            self.save_file = False
            print("Stop Saving Data")
            self.file.close()
        else:
            print("File Opened, Saving Data")
            self.save_file = True
            self.file = open(".\data" + datetime.now().strftime("\%y-%m-%d_%H-%M-%S")+'log.csv', 'a+')



    def calibrate_axis(self, axis_index):
        num_samples = 1000
        calibration_array = np.zeros((num_samples,2))
        axis = ['X', 'Y', 'Z']
        # tell user to put 'axis' up. count down in terminal 3, 2, 1, recording..... 
        print("Set up for positive "+ axis[axis_index])
        sleep(1)
        print("starting positive "+axis[axis_index]+" calibration")
        while((len(calibration_array) < num_samples) and (not self.serial_monitor.data.empty())) :
            data_point = self.serial_monitor.data.get()
            calibration_array.append(data_point[axis])
    
        print("Set up for negative "+ axis[axis_index] )
        sleep(2)
        print("starting negative "+axis[axis_index]+" calibration")

        
        # tell user 'averaging samples....'
        # set up for negative 'axis'
        # count down 3, 2, 1, recoring....
        # print avg +1,-1,zero crossing 
        # Set the axis values in self.axis_zero and self.axis_sensitivity arrays
        # decide if this should be used to scale data at time of plotting or change y_offset and y_scale?
        
    def shift_data(self, data_point):
        shifted_data_point = [0,0,0]
        for i in range(len(data_point)):
            shifted_data_point[i] = (data_point[i] - self.axis_zero[i])  / self.axis_sensitivity[i]
        return shifted_data_point
        
    def run_loop(self):
        # arrays to store serial data for storage or plotting
        data_chunk = []
        data_rolling_plot = []

        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window

            # Handle keyboard commands and user input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        try:
                            self.toggle_save_data()
                        except:
                            print("Invalid input. Sample rate should be a positive integer")
                    if event.key == pygame.K_b:
                        try:
                            time_base = float(input("Enter new time base (sec / division) in seconds: "))
                            if (time_base >0 and time_base <= 10):
                                self.time_base = time_base
                                self.set_plot_timing()
                                print("Seconds per Division set to :" + str(self.time_base))
                            else:
                                print("Time base must be between 0.0 seconds and 10.0 seconds")
                        except:
                            print("Invalid input. Time base should be a positive number between 0 and 60.0")
                    if event.key == pygame.K_c:
                        try:
                            cutoff_freq = float(input("Enter digital filter cutoff frequency in Hz: "))
                            if 0 < cutoff_freq and cutoff_freq < self.sample_rate / 2:
                                self.cutoff_freq = cutoff_freq
                                self.set_plot_timing()
                                print("Cutoff set to " + str(self.cutoff_freq)  + " Hz")
                            elif cutoff_freq == 0:
                                self.cutoff_freq = self.sample_rate/2 - .01
                                self.set_plot_timing()
                                print("Cutoff frequency set to Nyquist frequency")
                            else:
                                print("Cutoff frequency must be between 0 and" + str(self.sample_rate/2))
                        except:
                            print("Cutoff frequency must be a number between 0 and " + str(self.sample_rate /2))
                    if event.key == pygame.K_SPACE:
                        self.pause_plot = not self.pause_plot
                        print("Plot paused: " + str(self.pause_plot))
                    if event.key == pygame.K_t:
                        self.use_triggering = not self.use_triggering
                        self.set_plot_timing()
                        print("Rising Edge Trigger: " + str(self.use_triggering))
                    if event.key == pygame.K_f:
                        self.plot_filtered = not self.plot_filtered
                        print("Plot filtered data: " + str(self.plot_filtered))
                    if event.key == pygame.K_x:
                        print("begin X calibration")
                        self.calibrate_axis(0)
                    if event.key == pygame.K_x:
                        print("begin Y calibration")
                        self.calibrate_axis(1)
                    if event.key == pygame.K_z: 
                        print("Begin Z calibration")
                        self.calibrate_axis(2)

            # draw background to wipe away anything from last frame, draw plot grid
            self.draw_background()


            # get data from background thread:
            while not self.serial_monitor.data.empty():
                data_point = self.serial_monitor.data.get()
                data_chunk.append(data_point[:])
                shifted_data = self.shift_data(data_point[:])
                data_rolling_plot.append(shifted_data)
                if len(data_chunk) == self.data_chunk_size:
                    # we have a complete chunk of data so save to file
                    if self.save_file:
                        for row in data_chunk:
                            for i in range(self.serial_monitor.num_channels):
                                raw_val = row[i]
                                g_converted_val = (raw_val - self.axis_zero[i])/ self.axis_sensitivity[i]
                                if self.save_g_data:
                                    self.file.write(str(g_converted_val) + ',')
                                else:
                                    self.file.write(str(raw_val) + ',')
                                    
                            self.file.write('\n')

                    # reset the data chunk
                    data_chunk = []

            # plot the traces
            overage = len(data_rolling_plot) - self.plot_len
            if self.use_triggering or self.plot_filtered:
                try:
                    data_rolling_plot_filtered = self.filter.apply_filter(data_rolling_plot)
                except:
                    data_rolling_plot_filtered = data_rolling_plot
                    print("Unable to filter data")
    
                if overage > 0:
                    del data_rolling_plot_filtered[0:overage]
              
            if overage > 0:
                del data_rolling_plot[0:overage]

            if self.plot_filtered:
                final_plot_data = data_rolling_plot_filtered
            else:
                final_plot_data = data_rolling_plot

            start_index = 0
            if self.use_triggering:
                start_index = self.find_trig_index(data_rolling_plot_filtered[0:self.plot_len_visible],0,618)

            for j in range(self.serial_monitor.num_channels):
                # plot the data

                trace = [[self.time_range[i - start_index], -self.y_scale * final_plot_data[i][j] - self.y_offset + self.height] for i
                            in range(start_index, int(min(len(final_plot_data), self.plot_len_visible + start_index)))]
                if len(trace) > 1:
                    pygame.draw.aalines(self.screen, self.channel_color[j], False, trace)

                if self.debug_mode:
                    print("start index: " + str(start_index))
                    print("len array: " + str(len(data_rolling_plot)))
                    print("plot len: " + str(self.plot_len))
                    print("plot len visible: " + str(self.plot_len_visible))
                    print("plot len: " + str(self.plot_len))

            
            # flip() the display to put your work on screen
            if not self.pause_plot:
                pygame.display.flip()
            self.clock.tick(self.fps)  # limits FPS 

        # runs when window x is pressed:
        pygame.quit()
        self.end_animation()



# program entry point:
if __name__ == '__main__':
    my_animation = Animate()
