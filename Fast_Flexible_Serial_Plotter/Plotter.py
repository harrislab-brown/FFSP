#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thursday Sep 21 2023

@author: eli
"""

import pygame
import numpy as np

class Plotter:
    
    def __init__(self, display, grid=True, real_time=True, filt_data=True, trig_points=True):

        # pygame window parameters:
        self.display = display
        self.fps = 30
        self.width, self.height = 800,400
        self.padding = 20
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.red = '0xab250e'
        self.red_trig = '0xd46450'
        self.grn = '0x1aab40'
        self.grn_trig = '0x8ce6a4'
        self.blu = '0x6f46db'
        self.grid_color = '0x727575'

        self.plot_grid = grid
        self.plot_real_time = real_time
        self.plot_filt_data = filt_data
        self.plot_trig_points = trig_points


        # plotting parameters:
        self.plot_len = 2500
        self.plot_queue = []
        self.plot_y_scale = self.height / 10

    def plot_queue_push(self, value):
        self.plot_queue.append(value)

    def tick(self):
        self.clock.tick(self.fps)   


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
        

    def plot_channels(self):
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


    def plot_filtered_output(self, filt_data_arr, x_trig_i, y_trig_i):
        self.filt_data_arr = filt_data_arr
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
        [pygame.draw.circle(self.screen,self.red_trig,x_plt_trace[i],2) for i in x_trig_i]
        [pygame.draw.circle(self.screen,self.grn_trig,y_plt_trace[i],2) for i in y_trig_i]

    def plot_text(self, x_avg, y_avg, z_avg):
        #display animation fps:
        #fps = self.font.render( str(int(self.clock.get_fps())) ,True,'white')
        #self.screen.blit(fps,(self.padding + self.width/10, self.padding))

        #display accel_averages:
        ax = self.font.render('X": ' + str(x_avg), True, self.red)
        ay = self.font.render('Y": ' + str(y_avg), True, self.grn)
        az = self.font.render('Z": ' + str(z_avg), True, self.blu)
        self.screen.blit(ax, (3*self.width/10, self.padding))
        self.screen.blit(ay, (5*self.width/10, self.padding))
        self.screen.blit(az, (7*self.width/10, self.padding))