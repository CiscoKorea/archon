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

from archon import *
from common import *

def ep_all(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    eps = M.Endpoint.list(detail=True, sort='dn', page=(0,10))
    
    #===========================================================================
    # Logic
    #===========================================================================
    table = DataTable(V('Domain'), V('Name'), V('EPG'), V('Path'), V('Encap'), V('IP'), V('NIC Type'))
    ep_cnt = 0
    dcv_cnt = 0
    mng_cnt = 0
    phy_cnt = 0
    hyp_cnt = 0
    vir_cnt = 0
    
    for domain_name in M:
        
        paths = M[domain_name].Class('fvRsCEpToPathEp').list()
        nics = M[domain_name].Class('compNic').list(detail=True)
        
        for ep in eps[domain_name]:
            ep_cnt += 1
            dn = ep['dn']
            mac = ep['mac']
            if 'epg-' in dn:
                epg_name = '<small>%s</small>' % re.sub('(uni/|tn-|ap-|epg-|/cep-[a-zA-Z0-9:]+)', '', dn)
                nic_type = ' '
                for nic in nics:
                    if mac == nic['mac']:
                        if nic.class_name == 'compDNic':
                            dcv_cnt += 1
                            nic_type += '<p><small>Discovered,&nbsp;</small></p>'
                        elif nic.class_name == 'compMgmtNic':
                            mng_cnt += 1
                            nic_type += '<p><small>Management : ' + re.sub('(comp/|prov-|ctrlr-|hv-|mgmtnic-|\[|\])', '', nic['dn']) + ',&nbsp;</small></p>'
                        elif nic.class_name == 'compHpNic':
                            hyp_cnt += 1
                            nic_type += '<p><small>Hypervisor : ' + re.sub('(comp/|prov-|ctrlr-|hv-|hpnic-|\[|\])', '', nic['dn']) + ',&nbsp;</small></p>'
                        elif nic.class_name == 'compPpNic':
                            phy_cnt += 1
                            nic_type += '<p><small>Physical,&nbsp;</small></p>'
                        elif nic.class_name == 'compVNic':
                            vir_cnt += 1
                            nic_type += '<p><small>Virtual : ' + re.sub('(comp/|prov-|ctrlr-|vm-|/vnic-[a-zA-Z0-9:]+|\[|\])', '', nic['dn']) + ',&nbsp;</small></p>'
            else:
                epg_name = ' '
                nic_type = 'Logical Device'
            ip = ep['ip']
            encap = ep['encap']
            
            intf = ' '
            for path in paths:
                if dn in path['dn']:
                    intf = path['dn'].split(dn + '/rscEpToPathEp-')[1]
                    intf = re.sub('(topology/|pod-|protpaths-|paths-|pathep-|\[|\])', '', intf)
            
            table.Record(domain_name,
                         Get('/aci/show/endpoint/%s/%s' % (domain_name, dn)).html(mac),
                         epg_name, intf, encap, ip, nic_type)
    
    #===========================================================================
    # View
    #===========================================================================
    V.Page.html(
        ROW().html(
            COL(2).html(CountPanel(V('Endpoints'), 'plug', ep_cnt, **{'class' : 'panel-dgrey'})),
            COL(2).html(CountPanel(V('Discovered'), 'flag-checkered', dcv_cnt, **{'class' : 'panel-dgrey'})),
            COL(2).html(CountPanel(V('Management'), 'cog', mng_cnt, **{'class' : 'panel-dgrey'})),
            COL(2).html(CountPanel(V('Physical'), 'server', phy_cnt, **{'class' : 'panel-dgrey'})),
            COL(2).html(CountPanel(V('Hypervisor'), 'cubes', hyp_cnt, **{'class' : 'panel-dgrey'})),
            COL(2).html(CountPanel(V('Virtual'), 'cube', vir_cnt, **{'class' : 'panel-dgrey'}))
        )
    ).html(table)
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

def ep_one(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    domain_name = R.Path[3]
    dn = '/'.join(R.Path[4:])
    ep = M[domain_name](dn, detail=True)
    
    #===========================================================================
    # Logic    
    #===========================================================================
    nav = Navigation()
    
    # Details
    kv = KeyVal()
    for key in ep.keys(): kv.Data(key, ep[key])
    nav.Tab(V('Details'), kv)
    
    # Topology
    topo = Topo()
    set_topo(topo, dn, color='red', path_color='orange', dot=True)
    nav.Tab(V('Topology'), DIV(style='text-align:center;padding-top:10px;').html(topo))
    
    # EPG
    epg = ep.parent(detail=True)
    if epg and epg.class_name == 'fvAEPg':
        kv = KeyVal()
        for key in epg.keys(): kv.Data(key, epg[key])
        nav.Tab(V('EPG'), kv)
        
    # Path
    children = ep.children(detail=True)
    for child in children:
        if child.class_name == 'fvRsCEpToPathEp':
            kv = KeyVal()
            for key in child.keys(): kv.Data(key, child[key])
            nav.Tab(V('Path'), kv)
            set_topo(topo, child['tDn'])
            topo.Edge(dn, child['tDn'])
            break
    
    # Interface & Host
    hosts = []
    nics = M[domain_name].Class('compNic').list(mac=ep['mac'], detail=True)
    if nics:
        nicdiv = DIV()
        hstdiv = DIV()
        nav.Tab(V('Network Interface'), nicdiv)
        nav.Tab(V('Hosts'), hstdiv)
        
        phy_nic = None
        vm_nic = None
        hv_nic = None
        mg_nic = None
        
        phy_host = None
        vm_host = None
        hv_host = None
        
        for nic in nics:
            key = nic.keys()
            host = nic.parent(detail=True)
            if nic.class_name == 'compPpNic':
                if phy_nic == None: phy_nic = FooTable(*['+' + k if k != 'name' else V('Physical NIC') for k in key])
                phy_nic.Record(*[nic[k] for k in key])
                set_topo(topo, nic['dn'], color='green', path_color='green')
                topo.Edge(dn, nic['dn'])
                if host and host['dn'] not in hosts:
                    hosts.append(host['dn'])
                    key = host.keys()
                    if phy_host == None: phy_host = FooTable(*['+' + k if k != 'name' else V('Physical Hosts') for k in key])
                    phy_host.Record(*[host[k] for k in key])
            elif nic.class_name == 'compVNic':
                if vm_nic == None: vm_nic = FooTable(*['+' + k if k != 'name' else V('Virtual NIC') for k in key])
                vm_nic.Record(*[nic[k] for k in key])
                set_topo(topo, nic['dn'], color='green', path_color='green')
                topo.Edge(dn, nic['dn'])
                if host and host['dn'] not in hosts:
                    hosts.append(host['dn'])
                    key = host.keys()
                    if vm_host == None: vm_host = FooTable(*['+' + k if k != 'name' else V('Virtual Hosts') for k in key])
                    vm_host.Record(*[host[k] for k in key])
            elif nic.class_name == 'compHpNic':
                if hv_nic == None: hv_nic = FooTable(*['+' + k if k != 'name' else V('Hypervisor NIC') for k in key])
                hv_nic.Record(*[nic[k] for k in key])
                set_topo(topo, nic['dn'], color='green', path_color='green')
                topo.Edge(dn, nic['dn'])
                if host and host['dn'] not in hosts:
                    hosts.append(host['dn'])
                    key = host.keys()
                    if hv_host == None: hv_host = FooTable(*['+' + k if k != 'name' else V('Hypervisor Hosts') for k in key])
                    hv_host.Record(*[host[k] for k in key])
            elif nic.class_name == 'compMgmtNic':
                if mg_nic == None: mg_nic = FooTable(*['+' + k if k != 'name' else V('Management NIC') for k in key])
                mg_nic.Record(*[nic[k] for k in key])
                set_topo(topo, nic['dn'], color='green', path_color='green')
                topo.Edge(dn, nic['dn'])
                if host and host['dn'] not in hosts:
                    hosts.append(host['dn'])
                    key = host.keys()
                    if hv_host == None: hv_host = FooTable(*['+' + k if k != 'name' else V('Hypervisor Hosts') for k in key])
                    hv_host.Record(*[host[k] for k in key])
        
    #===========================================================================
    # View
    #===========================================================================
        if phy_nic != None: nicdiv.html(phy_nic)
        if vm_nic != None: nicdiv.html(vm_nic)
        if hv_nic != None: nicdiv.html(hv_nic)
        if mg_nic != None: nicdiv.html(mg_nic)
        if phy_host != None: hstdiv.html(phy_host)
        if vm_host != None: hstdiv.html(vm_host)
        if hv_host != None: hstdiv.html(hv_host)
    
    V.Page.html(HEAD(1).html(ep['name']))
    V.Page.html(
        HEAD(3).html('Layer 2'),
        HEAD(4).html(ep['mac'] + ' ' + ep['encap']),
        HEAD(3).html('Layer 3'),
        HEAD(4).html(ep['ip'])
    )
    V.Page.html(nav)
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))
