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

import time

import pygics
import acidipy
import archon

from archon import *
from models import *
from .settings import *
from acitoolkit.acitoolkit import AppProfile

#===============================================================================
# Create your manager here.
#===============================================================================

class HealthMonitor(pygics.Task):
    
    def __init__(self, manager):
        pygics.Task.__init__(self, tick=HEALTH_MON_SEC)
        self.manager = manager
        self.health = {'_tstamp' : []}
        for i in reversed(range(0, HEALTH_MON_CNT)):
            self.health['_tstamp'].append('00:00:00')
        self.start()
        
    def getNewHealthHist(self, dn, score):
        if dn in self.health:
            ret = self.health[dn][1:]
            ret.append(score)
            return ret
        else:
            ret = []
            for i in range(0, HEALTH_MON_CNT - 1): ret.append(0)
            ret.append(score)
            return ret
        
    def getHealth(self):
        return self.health
    
    def __run__(self):
        now = time.strftime("%H:%M:%S", time.localtime(time.time()))
        
        total, pod, node, tenant, appprof, epg = Burst(
        )(self.manager.health
        )(self.manager.Pod.health
        )(self.manager.Node.health
        )(self.manager.Tenant.health
        )(self.manager.AppProfile.health
        )(self.manager.EPG.health
        ).do()
        
        health = {'_tstamp' : self.health['_tstamp'][1:]}
        health['_tstamp'].append(now)
        
        for dom_name in total: health[dom_name] = self.getNewHealthHist(dom_name, total[dom_name]['score'])
        for dom_name in pod:
            for dp in pod[dom_name]:
                dn = dom_name + '/' + dp['dn']
                health[dn] = self.getNewHealthHist(dn, dp['score'])
        for dom_name in node:
            for dp in node[dom_name]:
                dn = dom_name + '/' + dp['dn']
                health[dn] = self.getNewHealthHist(dn, dp['score'])
        for dom_name in tenant:
            for dp in tenant[dom_name]:
                dn = dom_name + '/' + dp['dn']
                health[dn] = self.getNewHealthHist(dn, dp['score'])
        for dom_name in appprof:
            for dp in appprof[dom_name]:
                dn = dom_name + '/' + dp['dn']
                health[dn] = self.getNewHealthHist(dn, dp['score'])
        for dom_name in epg:
            for dp in epg[dom_name]:
                dn = dom_name + '/' + dp['dn']
                health[dn] = self.getNewHealthHist(dn, dp['score'])
        
        self.health = health
    
class EndpointTracker(acidipy.Event):
    
    @classmethod
    def initDatabase(cls):
        EPTracker.objects.all().delete()
        pass
    
    def __init__(self, manager, domain_name):
        self.manager = manager
        self.domain_name = domain_name
        self.getInitData()
        
    def convertTstamp(self, tstamp):
        (resp_ts, remaining) = tstamp.split('T')
        resp_ts += ' '
        resp_ts = resp_ts + remaining.split('+')[0].split('.')[0]
        return resp_ts
    
    def getIfName(self, ep):
        epcs = ep.Class('fvRsCEpToPathEp').list(sort='dn')
        if_dn = []
        for epc in epcs:
            if_dn.append(re.sub('(topology/|pod-|protpaths-|paths-|pathep-|\[|\])', '', epc['tDn']))
        return if_dn
    
    def getInitData(self):
        ep_list = self.manager[self.domain_name].Endpoint.list(detail=True)
        for ep in ep_list:
            sdn = ep['dn'].split('/')
            start = self.convertTstamp(ep['modTs'])
            create = False
            
            epts = EPTracker.objects.filter(domain=self.domain_name,
                                            dn=ep['dn'],
                                            stop='Active')
            
            if len(epts) != 0:
                for ept in epts:
                    if ept.start != start:
                        ept.stop = start
                        ept.save()
                        create = True
            else: create = True
            if create:
                EPTracker.objects.create(mac=ep['mac'],
                                         ip=ep['ip'],
                                         domain=self.domain_name,
                                         tenant=sdn[1].replace('tn-', ''),
                                         app=sdn[2].replace('ap-', ''),
                                         epg=sdn[3].replace('epg-', ''),
                                         dn=ep['dn'],
                                         intf=','.join(self.getIfName(ep)),
                                         start=self.convertTstamp(ep['modTs']),
                                         stop='Active')
            
    def handle(self, status, obj):
        if self.manager.debug: print('[Info]Archon:ACI:Manager:EPTracker:%s:%s:%s' % (obj.class_name, status, obj))
        
        sdn = obj['dn'].split('/')
        start = self.convertTstamp(obj['modTs'])
        
        epts = EPTracker.objects.filter(domain=self.domain_name,
                                        dn=obj['dn'],
                                        stop='Active')
        
        for ept in epts:
            if ept.start != start:
                ept.stop = start
                ept.save()
        
        if status != 'deleted':
            EPTracker.objects.create(mac=obj['mac'],
                                     ip=obj['ip'],
                                     domain=self.domain_name,
                                     tenant=sdn[1].replace('tn-', ''),
                                     app=sdn[2].replace('ap-', ''),
                                     epg=sdn[3].replace('epg-', ''),
                                     dn=obj['dn'],
                                     intf=','.join(self.getIfName(obj)),
                                     start=self.convertTstamp(obj['modTs']),
                                     stop='Active')

class Manager(acidipy.MultiDomain, archon.ManagerAbstraction):
    
    def __init__(self):
        acidipy.MultiDomain.__init__(self, debug=MANAGER_DEBUG)
        domains = Domain.objects.all()
        for domain in domains:
            ret = acidipy.MultiDomain.addDomain(self, domain.name, domain.controllers, domain.user, domain.password)
            if ret:
                self[domain.name].eptracker = EndpointTracker(self, domain.name)
                self[domain.name].Endpoint.event(self[domain.name].eptracker)
        self.healthmon = HealthMonitor(self)
    
    def addDomain(self, domain_name, ip, user, pwd):
        try: Domain.objects.get(name=domain_name)
        except:
            ret = acidipy.MultiDomain.addDomain(self, domain_name, ip, user, pwd)
            if ret:
                Domain.objects.create(name=domain_name, controllers=ip, user=user, password=pwd)
                self[domain_name].eptracker = EndpointTracker(self, domain_name)
                self[domain_name].Endpoint.event(self[domain_name].eptracker)
            return ret
        return False
    
    def delDomain(self, domain_name):
        try: domain = Domain.objects.get(name=domain_name)
        except: return False
        acidipy.MultiDomain.delDomain(self, domain_name)
        domain.delete()
        return True
    
    def initEndpoint(self):
        EndpointTracker.initDatabase()
        for domain_name in self: self[domain_name].eptracker.getInitData()
        
    def getHealth(self):
        return self.healthmon.getHealth()
    
    def getSummary(self, R, M, V):
        return {
            'name' : 'ACI',
            'icon' : 'aci/APIC_Default.png',
            'desc' : 'Application Centric Infrastructure Monitoring Application',
            'link' : '/aci/overview',
            'view' : DIV()
        }
