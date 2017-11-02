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

def contract_all(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    ctrts, subjs, provs, conss = Burst(
    )(M.Contract.list, detail=True, sort='dn'
    )(M.Subject.list, sort='dn'
    )(M.Class('vzRtProv').list, sort='dn'
    )(M.Class('vzRtCons').list, sort='dn'
    ).do()
    
    #===========================================================================
    # Logic
    #===========================================================================
    table = TABLE.BASIC(V('Domain'), V('Name'), V('Scope'), V('Subject'), V('Provider'), V('Consumer'))
    ctrt_cnt = 0
    prov_cnt = 0
    cons_cnt = 0
    for domain_name in sorted(M.keys()):
        for ctrt in ctrts[domain_name]:
            ctrt_cnt += 1
            dn = ctrt['dn']
            path, _, rn = ctrt.ident()
            path = re.sub('(uni/|tn-)', '', path)
            name = PARA().html(SMALL().html(path + '/'), GET('/aci/show/contract/%s/%s' % (domain_name, dn)).html(rn))
            ctrt_subj = ' '
            ctrt_prov = ' '
            ctrt_cons = ' '
            
            for subj in subjs[domain_name]:
                if dn in subj['dn']: ctrt_subj += '<p><small>' + subj['name'] + ',&nbsp;</small></p>'
            for prov in provs[domain_name]:
                if dn in prov['dn']:
                    prov_cnt += 1
                    ctrt_prov += '<p><small>' + re.sub('/\w+-', '/', prov['tDn']).replace('uni/', '') + ',&nbsp;</small></p>'
            for cons in conss[domain_name]:
                if dn in cons['dn']:
                    cons_cnt += 1
                    ctrt_cons += '<p><small>' + re.sub('/\w+-', '/', cons['tDn']).replace('uni/', '') + ',&nbsp;</small></p>'
            
            table.Record(domain_name, name, ctrt['scope'], ctrt_subj, ctrt_prov, ctrt_cons)
    
    #===========================================================================
    # View
    #===========================================================================
    V.Page.html(
        ROW().html(
            COL(4).html(COUNTER(V('Contracts'), 'ticket', ctrt_cnt, CLASS='panel-dgrey')),
            COL(4).html(COUNTER(V('Provider'), 'truck', prov_cnt, CLASS='panel-dgrey')),
            COL(4).html(COUNTER(V('Consumer'), 'shopping-cart', cons_cnt, CLASS='panel-dgrey'))
        )
    ).html(table)
    
    V.Menu.html(BUTTON(CLASS='btn-primary').click('/'.join(R.Path)).html(V('Refresh')))

def contract_one(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    domain_name = R.Path[3]
    dn = '/'.join(R.Path[4:])
    ctrt = M[domain_name](dn, detail=True)
    name = ctrt['name']
    
    #===========================================================================
    # Logic
    #===========================================================================
    nav = NAV()
    
    # Details
    kv = KEYVAL()
    for key in ctrt.keys(): kv.Data(key, ctrt[key])
    nav.Tab(V('Details'), kv)
    
    # Topology
    topo = TOPO()
    set_topo(topo, dn, color='red', path_color='orange', dot=True)
    nav.Tab(V('Topology'), DIV(STYLE='text-align:center;padding-top:10px;').html(topo))
    
    # Subject
    datas = ctrt.Subject.list(detail=True, sort='dn')
    if datas:
        key = ctrt.Subject.keys()
        table = TABLE.FLIP(*['+' + k if k != 'name' else V('Name') for k in key])
        for data in datas:
            table.Record(*[data[k] for k in key])
            set_topo(topo, data['dn'], color='orange')
            flts = data.Class('vzRsSubjFiltAtt').list(detail=True)
            for flt in flts:
                set_topo(topo, flt['tDn'], color='orange', path_color='orange')
                topo.Edge(data['dn'], flt['tDn'])
        nav.Tab(V('Subjects'), table)
    
    
    epg_key = M[domain_name].EPG.keys()
    epg_prov_table = TABLE.FLIP(*['+' + k if k != 'name' else V('Name') for k in epg_key])
    epg_cons_table = TABLE.FLIP(*['+' + k if k != 'name' else V('Name') for k in epg_key])
    
    ext_key = M[domain_name].Class('l3extInstP').keys()
    ext_prov_table = TABLE.FLIP(*['+' + k if k != 'name' else V('Name') for k in ext_key])
    ext_cons_table = TABLE.FLIP(*['+' + k if k != 'name' else V('Name') for k in ext_key])
    
    # Provided
    act = ctrt.Class('vzRtProv')
    datas = act.list(sort='dn', detail=True)
    if datas:
        for data in datas:
            if data['tCl'] == 'fvAEPg':
                epg = M[domain_name](data['tDn'], detail=True)
                epg_prov_table.Record(*[epg[k] for k in epg_key])
                set_topo(topo, epg['dn'], color='pink', path_color='orange')
                topo.Edge(dn, epg['dn'])
            elif data['tCl'] == 'l3extInstP':
                ext = M[domain_name](data['tDn'], detail=True)
                ext_prov_table.Record(*[ext[k] for k in ext_key])
                set_topo(topo, ext['dn'], color='pink', path_color='orange')
                topo.Edge(dn, ext['dn'])
    
    # Consumed
    act = ctrt.Class('vzRtCons')
    datas = act.list(sort='dn', detail=True)
    if datas:
        for data in datas:
            if data['tCl'] == 'fvAEPg':
                epg = M[domain_name](data['tDn'], detail=True)
                epg_cons_table.Record(*[epg[k] for k in epg_key])
                set_topo(topo, epg['dn'], color='cyan', path_color='orange')
                topo.Edge(dn, epg['dn'])
            elif data['tCl'] == 'l3extInstP':
                ext = M[domain_name](data['tDn'], detail=True)
                ext_cons_table.Record(*[ext[k] for k in ext_key])
                set_topo(topo, ext['dn'], color='cyan', path_color='orange')
                topo.Edge(dn, ext['dn'])
    
    if epg_prov_table: nav.Tab(V('Provider EPG'), epg_prov_table)
    if epg_cons_table: nav.Tab(V('Consumer EPG'), epg_cons_table)
    if ext_prov_table: nav.Tab(V('Provider L3 External'), ext_prov_table)
    if ext_cons_table: nav.Tab(V('Consumer L3 External'), ext_cons_table)
    
    #===========================================================================
    # View
    #===========================================================================
    V.Page.html(
        HEAD(1).html(name),
        nav
    )
    V.Menu.html(BUTTON(CLASS='btn-primary').click('/'.join(R.Path)).html(V('Refresh')))
