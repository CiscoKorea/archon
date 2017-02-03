# -*- coding: utf-8 -*-
################################################################################
#        _____ _                  _____           _                            #
#       / ____(_)                / ____|         | |                           #
#      | |     _ ___  ___ ___   | (___  _   _ ___| |_ ___ _ __ ___  ___        #
#      | |    | / __|/ __/ _ \   \___ \| | | / __| __/ _ \ '_ ` _ \/ __|       #
#      | |____| \__ \ (_| (_) |  ____) | |_| \__ \ ||  __/ | | | | \__ \       #
#       \_____|_|___/\___\___/  |_____/ \__, |___/\__\___|_| |_| |_|___/       #
#                                        __/ |                                 #
#                                       |___/                                  #
#           _  __                       _____       _  _____ ______            #
#          | |/ /                      / ____|     | |/ ____|  ____|           #
#          | ' / ___  _ __ ___  __ _  | (___   ___ | | (___ | |__              #
#          |  < / _ \| '__/ _ \/ _` |  \___ \ / _ \| |\___ \|  __|             #
#          | . \ (_) | | |  __/ (_| |  ____) | (_) | |____) | |____            #
#          |_|\_\___/|_|  \___|\__,_| |_____/ \___/|_|_____/|______|           #
#                                                                              #
################################################################################
#                                                                              #
# Copyright (c) 2016 Cisco Systems                                             #
# All Rights Reserved.                                                         #
#                                                                              #
# Licensed under the Apache License, Version 2.0 (the "License"); you may      #
# not use this file except in compliance with the License. You may obtain      #
# a copy of the License at                                                     #
#                                                                              #
# http://www.apache.org/licenses/LICENSE-2.0                                   #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT #
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the  #
#    License for the specific language governing permissions and limitations   #
#    under the License.                                                        #
#                                                                              #
################################################################################

from core import *

class Chart:
    
    ORDER_NON = 0
    ORDER_ASC = 1
    ORDER_DSC = 2
    
    COLOR_AUTO = 'A'
    COLOR_HEALTH = 'H'
    COLOR_UTIL = 'U'
    
    THEME_HEALTH = {'min' : 0, 'max' : 100, 'color' : COLOR_HEALTH}
    THEME_UTIL = {'min' : 0, 'max' : 100, 'color' : COLOR_UTIL}
    
    class __Chart__(VIEW):
        
        def __init__(self, chart_type, *labels, **options):
            VIEW.__init__(self, 'DIV', **{'id' : VIEW.getUUID(), 'lib' : 'dimple'})
            if 'width' not in options: options['width'] = None              # None : auto, else : fixed
            if 'height' not in options: options['height'] = None            # None : auto, else : fixed
            if 'margin' not in options: options['margin'] = ['30px', '20px', '20px', '20px']
            if 'min' not in options: options['min'] = None                  # None : auto, else : fixed
            if 'max' not in options: options['max'] = None                  # None : auto, else : fixed
            if 'xkey' not in options: options['xkey'] = 'X'                 # default : X
            if 'ykey' not in options: options['ykey'] = 'Y'                 # default : Y
            if 'xaxis' not in options: options['xaxis'] = True              # True : displayed, False : transparent
            if 'yaxis' not in options: options['yaxis'] = True              # True : displayed, False : transparent
            if 'order' not in options: options['order'] = Chart.ORDER_NON   # ORDER_NON, ORDER_ASC, ORDER_DSC 
            if 'color' not in options: options['color'] = Chart.COLOR_AUTO  # COLOR_AUTO, COLOR_HEALTH, COLOR_UTIL 
            if 'legend' not in options: options['legend'] = False           # True : displayed, False : transparent
            if 'tooltip' not in options: options['tooltip'] = True          # True : displayed, False : transparent
            if 'pivot' not in options: options['pivot'] = False             # True : pivoted, False : general
            if 'stack' not in options: options['stack'] = False             # True : stacked, False : general
            if 'size' not in options: options['size'] = 10                  # Donut Size
            
            if options['color'] == 'H' or options['color'] == 'U':
                self.rgcolor = True
                self.health_min = 100
                self.health_max = 0
                options['min_r'] = '0'
                options['min_g'] = '0'
                options['max_r'] = '0'
                options['max_g'] = '0'
            else: self.rgcolor = False
            
            self.labels = labels
            self.label_len = len(labels)
            self.xkey = options['xkey']
            self.ykey = options['ykey']
            self.options = options
            self.series = []
            self['chart'] = {
                'type' : chart_type,
                'labels' : self.labels,
                'series' : self.series,
                'options' : options
            }
        
        def __minmax__(self, val):
            if self.rgcolor:
                if val == None: val = 0
                if val < self.health_min: self.health_min = val
                if val > self.health_max: self.health_max = val
            return val
        
        def __rgcalc__(self):
            if self.rgcolor:
                if self.options['color'] == 'H':
                    self.options['min_r'] = str(255 - int((self.health_min * 255) / 100))
                    self.options['min_g'] = str(int((self.health_min * 255) / 100))
                    self.options['max_r'] = str(255 - int((self.health_max * 255) / 100))
                    self.options['max_g'] = str(int((self.health_max * 255) / 100))
                elif self.options['color'] == 'U':
                    self.options['min_r'] = str(int((self.health_min * 255) / 100))
                    self.options['min_g'] = str(255 - int((self.health_min * 255) / 100))
                    self.options['max_r'] = str(int((self.health_max * 255) / 100))
                    self.options['max_g'] = str(255 - int((self.health_max * 255) / 100))
            return self

    class Line(__Chart__):
          
        def __init__(self, *labels, **options):
            Chart.__Chart__.__init__(self, 'line', *labels, **options)
             
        def Data(self, series, *vals):
            datasets = []
            for i in range(0, self.label_len):
                datasets.append({self.xkey : self.labels[i], self.ykey : self.__minmax__(vals[i])})
            self.series.append({'series' : series, 'datasets' : datasets})
            return self.__rgcalc__()
        
    class Bar(__Chart__):
         
        def __init__(self, *labels, **options):
            Chart.__Chart__.__init__(self, 'bar', *labels, **options)
             
        def Data(self, series, *vals):
            for i in range(0, self.label_len):
                self.series.append({self.xkey : self.labels[i], 'series' : series, self.ykey : self.__minmax__(vals[i])})
            return self.__rgcalc__()
    
    class Pie(__Chart__):
        
        def __init__(self, *labels, **options):
            Chart.__Chart__.__init__(self, 'pie', *labels, **options)
             
        def Data(self, series, *vals):
            datasets = []
            for i in range(0, self.label_len):
                datasets.append({self.xkey : self.labels[i], self.ykey : self.__minmax__(vals[i])})
            self.series.append({'series' : series, 'datasets' : datasets})
            return self.__rgcalc__()
    
    class Donut(__Chart__):
        def __init__(self, *labels, **options):
            Chart.__Chart__.__init__(self, 'donut', *labels, **options)
             
        def Data(self, series, *vals):
            datasets = []
            for i in range(0, self.label_len):
                datasets.append({self.xkey : self.labels[i], self.ykey : self.__minmax__(vals[i])})
            self.series.append({'series' : series, 'datasets' : datasets})
            return self.__rgcalc__()

class Figure:
    
    COLOR_AUTO = 'A'
    COLOR_HEALTH = 'H'
    COLOR_UTIL = 'U'
    
    THEME_HEALTH = {'min' : 0, 'max' : 100, 'color' : COLOR_HEALTH}
    THEME_UTIL = {'min' : 0, 'max' : 100, 'color' : COLOR_UTIL}

    class __Figure__(VIEW):
        
        def __init__(self, figure_type, *vals, **options):
            VIEW.__init__(self, 'SPAN', **{'id' : VIEW.getUUID(), 'lib' : 'peity'})
            if 'color' in options: color = options.pop('color')
            else: color = Figure.COLOR_AUTO
            self['figure'] = {'type' : figure_type, 'color' : color, 'options' : options}
            self.html(','.join(str(s) for s in vals))

    class Line(__Figure__):
        
        def __init__(self, *vals, **options):
            Figure.__Figure__.__init__(self, 'line', *vals, **options)
            if len(vals) > 0 and vals[-1] != None: self['figure']['cval'] = vals[-1]
            else: self['figure']['cval'] = 0

    class Bar(__Figure__):
        
        def __init__(self, *vals, **options):
            Figure.__Figure__.__init__(self, 'bar', *vals, **options)
    
    class Pie(__Figure__):
        
        def __init__(self, *vals, **options):
            Figure.__Figure__.__init__(self, 'pie', *vals, **options)
            if len(vals) > 0 and vals[0] != None: self['figure']['cval'] = vals[0]
            else: self['figure']['cval'] = 0
    
    class Donut(__Figure__):
        
        def __init__(self, *vals, **options):
            if 'hole' in options: options['innerRadius'] = options.pop('hole')
            Figure.__Figure__.__init__(self, 'donut', *vals, **options)
            if len(vals) > 0 and vals[0] != None: self['figure']['cval'] = vals[0]
            else: self['figure']['cval'] = 0

class Topo(VIEW):
    
    def __init__(self, **options):
        if 'width' not in options: options['width'] = 0
        if 'height' not in options: options['height'] = 400
        VIEW.__init__(self, 'CANVAS', **{'id' : VIEW.getUUID(), 'lib' : 'arbor', 'class' : 'arborwrapper'})
        self.nodes = {}
        self.edges = {}
        self['topo'] = {
            'datasets' : {'nodes' : self.nodes, 'edges' : self.edges},
            'options' : options
        }
    
    def Node(self, name, label=None, color='grey', dot=False):
        if label == None: label = name
        if dot: self.nodes[name] = {'label' : label, 'color' : color, 'shape' : 'dot'}
        else: self.nodes[name] = {'label' : label, 'color' : color}
        return self

    def Edge(self, src, dst, color='grey'):
        if src not in self.edges: self.edges[src] = {}
        self.edges[src][dst] = {}
        return self
    
    def __len__(self, *args, **kwargs):
        return self.nodes.__len__()
    
    def isNode(self, name):
        if name in self.nodes: return True
        return False

class Gauge(VIEW):
    
    def __init__(self, title, value, min=0, max=100, **attrs):
        VIEW.__init__(self, 'DIV', **ATTR.merge(attrs, {'id' : VIEW.getUUID(), 'lib' : 'justgage'}))
        self['chart'] = {'title' : title, 'value' : value, 'min' : min, 'max' : max}
    
