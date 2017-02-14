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
from ..models import FaultMessage

def fault_all(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    if len(R.Path) > 3: faults = M.Fault.list(severity=R.Path[3], detail=True, sort='created|desc',page=(0,10))
    else: faults = M.Fault.list(detail=True, sort='created|desc', page=(0,10))
    
    #===========================================================================
    # Logic
    #===========================================================================
    table = DataTable(V('Domain'), V('Subjects'), V('Type'), V('Description'), V('Time Stamp'))
    cri_cnt = 0
    maj_cnt = 0
    min_cnt = 0
    war_cnt = 0
    
    for domain_name in M:
        for fault in faults[domain_name]:
            severity = fault['severity']
            if severity == 'critical':
                cri_cnt += 1
                attr = 'danger'
            elif severity == 'major':
                maj_cnt += 1
                attr = 'danger'
            elif severity == 'minor':
                min_cnt += 1
                attr = 'warning'
            elif severity == 'warning':
                war_cnt += 1
                attr = 'warning'
            elif severity == 'cleared':
                attr = 'success'
            else:
                attr = ''
            
            descr = StrWrap(400).html('<small>' + fault['descr'] + '</small>')
            tstamp = '<small>' + fault['created'][:-10] + '</small>'
            
            table.Record(domain_name,
                         Get('/aci/show/fault/%s/%s' % (domain_name, fault['dn'])).html(fault['subject']),
                         severity,
                         descr,
                         tstamp,
                         **{'class' : attr})
    
    #===========================================================================
    # View
    #===========================================================================
    if len(R.Path) < 4:
        V.Page.html(
            ROW().html(
                COL(3).html(CountPanel(V('Critical'), 'bolt', cri_cnt, **(ATTR.click('/aci/show/fault/critical') + {'class' : 'panel-red'}))),
                COL(3).html(CountPanel(V('Major'), 'exclamation-triangle', maj_cnt, **(ATTR.click('/aci/show/fault/major') + {'class' : 'panel-danger'}))),
                COL(3).html(CountPanel(V('Minor'), 'exclamation-circle', min_cnt, **(ATTR.click('/aci/show/fault/minor') + {'class' : 'panel-yellow'}))),
                COL(3).html(CountPanel(V('Warning'), 'exclamation', war_cnt, **(ATTR.click('/aci/show/fault/warning') + {'class' : 'panel-warning'})))
            )
        )
    V.Page.html(table)
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

def fault_one(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    domain_name = R.Path[3]
    dn = '/'.join(R.Path[4:])
    fault = M[domain_name](dn, detail=True)
    
    #===========================================================================
    # Logic
    #===========================================================================
    nav = Navigation()
    occur = V('From Instance') if fault.class_name == 'faultInst' else V('Delegated')
    title = '%s %s : %s' % (fault['type'].upper(), fault['severity'].upper(), fault['subject'])
    desc = fault['descr']
    
    # Guide
    try: guide = FaultMessage.objects.get(code=fault['code'])
    except: pass
    else:
        kv = KeyVal()
        kv.Data('Title', guide.title)
        kv.Data('Code', guide.code)
        kv.Data('Syslog', guide.syslog)
        kv.Data('Explanation', guide.explan)
        actions = guide.actions.split('\n')
        act = ''
        for i in range(0, len(actions)): act += ('<p><strong>Step%d</strong> : ' % (i + 1)) + actions[i] + '</p>'
        kv.Data('Actions', act)
        nav.Tab(V('Guide'), kv)
    
    # Details
    kv = KeyVal()
    for key in fault.keys(): kv.Data(key, fault[key])
    nav.Tab(V('Details'), kv)
    
    # Object
    if fault.class_name == 'faultInst': obj_dn = fault['dn'].split('/fault-')[0]
    elif fault.class_name == 'faultDelegate': obj_dn = fault['dn'].split('/fd-')[0]
    else: obj_dn = None
    if obj_dn != None:
        try: obj = M[domain_name](obj_dn, detail=True)
        except: pass
        else:
            kv = KeyVal()
            for key in obj.keys(): kv.Data(key, obj[key])
            nav.Tab(V('Object'), kv)
    
    #===========================================================================
    # View
    #===========================================================================
    V.Page.html(HEAD(1).html(title))
    if fault.class_name == 'faultInst':
        V.Page.html(
            HEAD(3).html('%s %s' % (fault['cause'], occur)),
            HEAD(4).html(obj_dn)
        )
    elif fault.class_name == 'faultDelegate':
        V.Page.html(
            HEAD(3).html('%s %s' % (fault['cause'], occur)),
            HEAD(4).html(fault['affected'])
        )
    V.Page.html(
        HEAD(3).html(V('Description')),
        HEAD(4).html(desc)
    )
    V.Page.html(nav)
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))
