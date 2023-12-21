import numpy as np
import pygame
from datetime import datetime
from SerialMonitor import SerialMonitor


class Animate:

    def __init__(self) -> None:

        # initialize the serial monitor
        # this starts the background thread to read the data
        # it also contains the data in a queue
        self.serial_monitor = SerialMonitor()
        self.data_chunk_size = 5000  # write to file every time we have this many data points

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
        self.grid_color = '0x727575'
<<<<<<< Updated upstream

        # plotting parameters:
        self.plot_len = self.data_chunk_size
        self.y_scale = self.height / 1023
        self.y_offset = 0
        self.plot_grid = True
=======
        self.text_color = '0xEEEEEE'
        self.channel_color = [self.red, self.grn, self.blu]

        # plotting parameters:
        self.sample_rate = 1_000 #sample rate in Hz. 10kHz is default for microcontroller on boot
        self.cutoff_freq = self.sample_rate /2 -.01
        self.time_base = .1 # seconds to display on the screen at a time (horizontal scale)
        #self.y_scale = self.height / 1023
        self.y_scale = self.height / 10000
        #self.y_offset = 0
        self.y_offset=self.height/2
        self.plot_grid = True
        self.plot_text = True
        self.use_triggering = False
        self.plot_filtered = False
        self.pause_plot = False
        self.set_plot_timing(self.sample_rate)
>>>>>>> Stashed changes

        # open output data file:
        self.save_file = True
        if self.save_file:
            self.file = open(".\data" + datetime.now().strftime("\%y-%m-%d_%H-%M-%S")+'log.csv', 'a+')

        # begin animation loop:
        self.run_loop()

    def draw_background(self):
        # fill screen to cover last frame
        self.screen.fill('0x313837')

        if not self.plot_grid:
            return
        num_vert_lines = 10
        num_hori_lines = 5
    
        for i in range(num_vert_lines+1): 
            y_val = i * self.height/num_vert_lines
            pygame.draw.line(self.screen,self.grid_color,(0,y_val),(self.width,y_val ))
        for i in range(num_hori_lines+1):
            x_val = i * (self.width-2*self.padding)/num_hori_lines
            pygame.draw.line(self.screen,self.grid_color,(x_val+self.padding,0),(x_val+self.padding,self.height))
        pygame.draw.line(self.screen,self.grid_color, (0,self.height/2),(self.width, self.height/2), 2 )

    def end_animation(self):
        self.serial_monitor.close()
        if self.save_file:
            self.file.close()

<<<<<<< Updated upstream
=======
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

>>>>>>> Stashed changes
    def run_loop(self):
        # arrays to store serial data for storage or plotting
        data_chunk = []
        data_rolling_plot = []

        # create regularly spaced x axis array:
        time_range = np.linspace(self.padding, self.width - self.padding, num=self.plot_len)

        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # draw background to wipe away anything from last frame, draw plot grid
            self.draw_background()
            
            # get data from background thread:
            while not self.serial_monitor.data.empty():
                data_point = self.serial_monitor.data.get()
                data_chunk.append(data_point[:])
                data_rolling_plot.append(data_point[:])

                if len(data_chunk) == self.data_chunk_size:
                    # we have a complete chunk of data so save to file
                    if self.save_file:
                        for row in data_chunk:
                            for i in range(self.serial_monitor.num_channels):
                                self.file.write(str(row[i]) + ',')
                            self.file.write('\n')

                    # reset the data chunk
                    data_chunk = []

            # plot the traces
            overage = len(data_rolling_plot) - self.plot_len
            if overage > 0:
                del data_rolling_plot[0:overage]

<<<<<<< Updated upstream
            if len(data_rolling_plot) > 1:
                for j in range(self.serial_monitor.num_channels):
                    # plot the data
                    trace = [[time_range[i], -self.y_scale * data_rolling_plot[i][j] - self.y_offset + self.height] for i
                             in range(len(data_rolling_plot))]
                    pygame.draw.aalines(self.screen, self.red, False, trace)
=======
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

>>>>>>> Stashed changes
            
            # flip() the display to put your work on screen
            pygame.display.flip()
            self.clock.tick(self.fps)  # limits FPS 

        # runs when window x is pressed:
        pygame.quit()
        self.end_animation()


# program entry point:
if __name__ == '__main__':
    my_animation = Animate()
