import serial
import numpy as np
import threading
from queue import Queue
import pygame
from datetime import datetime
from time import sleep
from scipy import signal

class Animate():

    def __init__(self) -> None:
        
        # check serial port of ESP32 device on your computer:
        self.serial_port = 'COM6'   ### CHANGE THIS TO MATCH YOUR COMPUTER ###
        # data storage variables:
        self.data_queue = Queue()
        self.data_arr = []
        self.filt_data_arr = []
        self.data_sample_len = 2500 # 5 seconds of data at 500Hz sample rate
        self.x_avg = 0
        self.y_avg = 0
        self.z_avg = 0
        self.x_trig_i = []
        self.y_trig_i = []

        # data snapshot save parameters:
        self.save_raw = True    # This is used to turn on the data snapshot function
                                # If True, self.data_arr will be saved to a file when the space bar is pressed
        self.save_raw_buffer = False

        # setup pygame window:
        pygame.init()
        self.fps = 30
        self.width, self.height = 800,400
        self.padding = 20
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.red = '0xab250e'
        self.red_trig = '0xd46450'
        self.grn = '0x1aab40'
        self.grn_trig = '0x8ce6a4'
        self.blu = '0x6f46db'
        self.grid_color = '0x727575'

        self.plot_grid = True
        self.plot_real_time = True
        self.plot_filt_data = True
        self.plot_trig_points = True

        # plotting parameters:
        self.plot_len = 2500
        self.plot_queue = []
        self.plot_y_scale = self.height / 10

        # setup data processing low pass filter:
        sample_rate = 500 # 0.5kHz sample frequency
        cutoff_freq = 50 # -3db frequency of filter in Hz
        self.filt_coeff_b, self.filt_coeff_a = signal.butter(3,cutoff_freq,'lowpass',fs=sample_rate)

        # setup serial port:     
        self.port = serial.Serial(self.serial_port, baudrate=115200, timeout=1 )
        print("port opened at: " + str(self.port.name))
        self.port_thread = threading.Thread(target=self.background_thread, args=(self.port,self.data_queue,))
        self.port_thread.start()
        sleep(.1)

        # open output data file:
        self.file = open(".\data"+ datetime.now().strftime("\%y-%m-%d_%H-%M-%S")+'_accel_log.csv','a+')
        self.file.write('timestamp,x_mean,x_std,y_mean,y_std,z_mean,z_std,dT_mean,dT_std\n')

        # begin animation loop:
        self.run_loop()

    def draw_background(self):
        #fill screen to cover last frame
        self.screen.fill('0x313837')

        if(self.plot_grid == False):
            return
        num_vert_lines =  10
        num_hori_lines = 5
    
        for i in range(num_vert_lines+1): 
            y_val = i * self.height/num_vert_lines
            pygame.draw.line(self.screen,self.grid_color,(0,y_val),(self.width,y_val ))
        for i in range(num_hori_lines+1):
            x_val = i * (self.width-2*self.padding)/num_hori_lines
            pygame.draw.line(self.screen,self.grid_color,(x_val+self.padding,0),(x_val+self.padding,self.height))
        pygame.draw.line(self.screen,self.grid_color, (0,self.height/2),(self.width, self.height/2), 2 )
        
    def plot_traces(self):
        overage = len(self.plot_queue) - self.plot_len
        if overage > 0:
            del self.plot_queue[0:overage]
        
        if( self.plot_real_time == False):
            return
        #create regularly spaced x axis:
        time_range = np.linspace(self.padding, self.width-self.padding, num=self.plot_len)
        
        x_plt_trace = [[time_range[i], -self.plot_y_scale*self.plot_queue[i][0]+self.height/2] for i in range(len(self.plot_queue))]
        y_plt_trace = [[time_range[i], -self.plot_y_scale*self.plot_queue[i][1]+self.height/2] for i in range(len(self.plot_queue))]
        z_plt_trace = [[time_range[i], -self.plot_y_scale*self.plot_queue[i][2]+self.height/2] for i in range(len(self.plot_queue))]
        pygame.draw.aalines(self.screen,self.red,False,x_plt_trace)
        pygame.draw.aalines(self.screen,self.grn,False,y_plt_trace)
        pygame.draw.aalines(self.screen,self.blu,False,z_plt_trace)        
    
    def plot_filtered_output(self):
        if(self.plot_filt_data == False):
            return
        if len(self.filt_data_arr) < self.plot_len: # if the filtered data array is not full, don't plot
            return
        self.filt_data_arr = self.filt_data_arr[:self.plot_len]
        time_range = np.linspace(self.padding, self.width-self.padding, num=self.plot_len)
        x_plt_trace = [[time_range[i],-self.plot_y_scale*self.filt_data_arr[i][0]+self.height/2] for i in range(self.plot_len)]
        y_plt_trace = [[time_range[i],-self.plot_y_scale*self.filt_data_arr[i][1]+self.height/2] for i in range(self.plot_len)]
        z_plt_trace = [[time_range[i],-self.plot_y_scale*self.filt_data_arr[i][2]+self.height/2] for i in range(self.plot_len)]
        pygame.draw.aalines(self.screen,self.red,False,x_plt_trace)
        pygame.draw.aalines(self.screen,self.grn,False,y_plt_trace)
        pygame.draw.aalines(self.screen,self.blu,False,z_plt_trace)

        if(self.plot_trig_points == False):
            return
        #plot circles at every point the code has detected a rising edge
        # pkpk values calculated between trigger points.
        [pygame.draw.circle(self.screen,self.red_trig,x_plt_trace[i],2) for i in self.x_trig_i]
        [pygame.draw.circle(self.screen,self.grn_trig,y_plt_trace[i],2) for i in self.y_trig_i]

    def end_animation(self):
        self.port_thread.join()
        self.file.close()

    def background_thread(self, port, data_queue):
        while(self.running):
            data_queue.put(port.readline())
    

    def process_and_save(self):

        # copy individual traces from data_arr to variables and apply LP filter to accel. data
        x_trace = signal.filtfilt( self.filt_coeff_b,self.filt_coeff_a, [item[0] for item in self.data_arr] )
        y_trace = signal.filtfilt( self.filt_coeff_b,self.filt_coeff_a, [item[1] for item in self.data_arr] )
        z_trace = signal.filtfilt( self.filt_coeff_b,self.filt_coeff_a, [item[2] for item in self.data_arr] )
        t_trace = [item[3] for item in self.data_arr]

        # array used for plotting filtered data:
        self.filt_data_arr = [[x_trace[i],y_trace[i],z_trace[i]] for i in range(self.plot_len)]
        
        # find max and min of each trace. Trigger threshold set at average of max and min
        x_max = np.max(x_trace)
        y_max = np.max(y_trace)
        x_min = np.min(x_trace)
        y_min = np.min(y_trace)
        x_trig = (x_max + x_min)/2 
        y_trig = (y_max + y_min)/2 

        # cycles are sections of data between rising edge trigger points
        # First and last cycles are thrown out since they may be incomplete
        x_cycle_count = 0
        x_cycle_list = []
        x_cycles = [] # empty list of lists, with list [0] initialized
        y_cycle_count = 0
        y_cycle_list = []
        y_cycles = []
        self.x_trig_i = [] # used to plot trigger points on filtered data plot
        self.y_trig_i = [] # 

        # iterate through data and cut into a list of cycles stored in {x/y}_cycles[]
        for i in range(len(x_trace)-1):

            x_cycle_list.append(x_trace[i])
            y_cycle_list.append(y_trace[i])
            if x_trace[i] < x_trig and x_trace[i+1] > x_trig:
                x_cycles.append(x_cycle_list)
                x_cycle_list = []
                x_cycle_count += 1
                self.x_trig_i.append(i)
            
            if y_trace[i] < y_trig and y_trace[i+1] > y_trig:
                y_cycles.append(y_cycle_list)
                y_cycle_list = []
                y_cycle_count += 1
                self.y_trig_i.append(i)

        # find the mean and std of peak-peak values for both x and y:
        x_pkpk = []
        y_pkpk = []
        for i in range(1,len(x_cycles)-1):
            x_pkpk.append(max(x_cycles[i]) - min(x_cycles[i]))
        for i in range(1,len(y_cycles)-1):
            y_pkpk.append(max(y_cycles[i]) - min(y_cycles[i]))

        # calculate mean and std of pkpk values to store. 
        # z and dT mean and std is calculated for entire trace since they should
        # be periodic so cycles are not well defined. 
        try:    
            x_mean =str(np.mean(x_pkpk).round(3))
            x_std = str(np.std(x_pkpk).round(3))
            y_mean = str(np.mean(y_pkpk).round(3))
            y_std = str(np.std(y_pkpk).round(3))
            z_mean = str(np.mean(z_trace).round(3))
            z_std = str(np.std(z_trace).round(3))
            t_mean = str(np.mean(t_trace).round(3))
            t_std = str(np.std(t_trace).round(3))
        except:
            print('error calculating MEAN or STD')
        
        # write data to file
        curr_time = datetime.now()
        timestamp = curr_time.strftime("%y-%m-%d_%H-%M-%S")
        print("save data at: " + curr_time.strftime("%H-%M-%S"))
        self.file.write(timestamp+','+x_mean+','+x_std+','+y_mean+','+y_std+','+z_mean+','+z_std+','+t_mean+','+t_std+'\n')
        
        self.x_avg = x_mean
        self.y_avg = y_mean
        self.z_avg = z_mean
        # reset data array:
        self.data_arr = []

    def save_snapshot(self):
        with open(".\data"+ datetime.now().strftime("\%y-%m-%d_%H-%M-%S")+'_raw_snapshot.csv','a+') as f_snapshot:
            f_snapshot.write('x_raw,y_raw,z_raw,dT_raw\n')
            curr_time = datetime.now()
            print("Saving Snapshot At: " + curr_time.strftime("%H-%M-%S"))
            for row in self.data_arr:
                f_snapshot.write(str(row[0])+','+str(row[1])+','+str(row[2])+','+str(row[3]) +'\n')
        self.save_raw_buffer = False

    def run_loop(self):
        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        print('Buffering Raw Data')
                        self.save_raw_buffer = True

            # draw background to wipe away anything from last frame, draw plot grid
            self.draw_background()
            
            # get data from background thread:
            while(self.data_queue.empty() == False):
                raw_data = (self.data_queue.get().decode('utf-8')) # decode binary string from serial port
                try:
                    # turn string into array of integers:
                    data = list(map(int, raw_data.strip("\r\n").split(" "))) 
                    # convert data from microvolts to G (accel) based on accelerometer datasheet specs:
                    g_data = list(map(lambda x: round(((x/1000000) - 1.615)/.3 , 3),data))
                    g_data[3] = round(data[3],3) # reset dT element to microseconds between samples (should not be scaled)
                
                    self.data_arr.append(g_data)
                    self.plot_queue.append(g_data)

                    # data array buffer is processed and stored when full
                    if(len(self.data_arr) == self.data_sample_len):
                        if (self.save_raw_buffer):
                            self.save_snapshot()
                        self.process_and_save()
                        
                except:
                    print('serial read error')
            
            # plot on the screen: 
            self.plot_traces()
            self.plot_filtered_output()
            
            #display animation fps:
            #fps = self.font.render( str(int(self.clock.get_fps())) ,True,'white')
            #self.screen.blit(fps,(self.padding + self.width/10, self.padding))
            #display accel_averages:
            ax = self.font.render('X": ' + str(self.x_avg), True, self.red)
            ay = self.font.render('Y": ' + str(self.y_avg), True, self.grn)
            az = self.font.render('Z": ' + str(self.z_avg), True, self.blu)
            self.screen.blit(ax, (3*self.width/10, self.padding))
            self.screen.blit(ay, (5*self.width/10, self.padding))
            self.screen.blit(az, (7*self.width/10, self.padding))
            
            # flip() the display to put your work on screen
            pygame.display.flip()
            self.clock.tick(self.fps)  # limits FPS 

        #runs when window x is pressed:
        pygame.quit()
        self.end_animation()


# program entry point:
if __name__=='__main__':
    my_animation = Animate()