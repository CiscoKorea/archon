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
from manager import Manager

#===============================================================================
# Create your views here.
#===============================================================================
@pageview(Manager)
def overview(R, M, V):
    if not M: V.Page.html(Alert(V('Info'), V('Non-exist ASA Connection'), **{'class' : 'alert-info'})); return
    
    health = M.getHealth()
    nats = M.NAT.Detail()
    pools = M.NAT.Pool()
    nat_count = M.NAT.Count()
    conn_count = M.Conn.Count()
    
    for domain_name in M:
        chart_hist = Chart.Line(height=145, min=0, max=100, *health['_tstamp'])
        chart_curr = Chart.Bar(V('CPU'), V('Memory'), V('Disk'), height=145, **Chart.THEME_UTIL)
        cpu_curr = 0
        mem_curr = 0
        disk_curr = 0
        for dn in health:
            if domain_name + '/cpu' in dn:
                chart_hist.Data(domain_name + '/CPU', *health[dn])
                cpu_curr = health[dn][-1]
            elif domain_name + '/mem' in dn:
                chart_hist.Data(domain_name + '/Memory', *health[dn])
                mem_curr = health[dn][-1]
            elif domain_name + '/disk' in dn:
                chart_hist.Data(domain_name + '/Disk', *health[dn])
                disk_curr = health[dn][-1]
        chart_curr.Data(V('Current'), cpu_curr, mem_curr, disk_curr)
        
        chart_conn = Chart.Bar(V('Max'), V('Current'),
                               height=40, margin=['65px', '0px', '20px', '20px'],
                               pivot=True, tooltip=False,
                               color=['rgba(128,177,211,0.8)', 'rgba(255,0,0,0.8)']
        ).Data(
            V('Connections'), conn_count[domain_name]['most_used'], conn_count[domain_name]['in_use'], 
        )
        
        chart_tran = Chart.Bar(V('Max'), V('Current'),
                               height=40, margin=['65px', '0px', '20px', '20px'],
                               pivot=True, tooltip=False,
                               color=['rgba(128,177,211,0.8)', 'rgba(255,0,0,0.8)']
        ).Data(
            V('NATs'), nat_count[domain_name]['most_used'], nat_count[domain_name]['in_use']
        )
        
        nat_table = DataTable(V('Config'), V('Mode'), V('From'), V('To'), V('Original'), V('Translate'), V('Trans-Hits'), V('Untrans-Hits'))
        for nat in nats[domain_name]:
            nat_table.Record(nat['config'], nat['mode'], nat['from'], nat['to'],
                             STRONG().html(nat['originalAddress']),
                             STRONG().html(nat['translatedAddress']),
                             str(nat['translateHits']), str(nat['untranslateHits']))
        
        pool_list = ROW()
        pats = {}
        
        for pool in pools[domain_name]:
            addr = '%s/%s' % (pool['address'], pool['proto'])
            if addr not in pats: pats[addr] = {'range' : [], 'count' : [], 'alloc' : [], 'total_count' : 0, 'total_alloc' : 0}
            rfreg = '%d-%d' % (pool['rangeStart'], pool['rangeEnd'])
            count = pool['rangeEnd'] - pool['rangeStart'] + 1
            alloc = pool['allocCount']
            pats[addr]['range'].append(rfreg)
            pats[addr]['count'].append(count)
            pats[addr]['alloc'].append(alloc)
            pats[addr]['total_count'] += count
            pats[addr]['total_alloc'] += alloc
        
        for addr in sorted(pats.keys()):
            pat = pats[addr]
            total_free = pat['total_count'] - pat['total_alloc']
            percent = (pat['total_alloc'] * 100.0) / pat['total_count']
            
            rfreg = DIV(style='text-align:center;width:200px;')
            for i in range(0, len(pat['range'])):
                rfreg.html(
                    SPAN(style='margin:0px 2px 0px 2px;').html(
                        Figure.Pie(pat['alloc'][i], pat['count'][i] - pat['alloc'][i], width=40, height=40, **Figure.THEME_UTIL),
                    ),
                    SPAN(style='position:absolute;transform:translateX(-42px);padding-top:14px;width:40px;text-align:center;').html(
                        STRONG().html('Seg%d' % (i + 1))
                    )
                )
            
            pool_list.html(
                COL(3, scr='sm', style='padding:0px 5px 0px 5px;').html(
                    DIV(style='width:200px;margin:auto;').html(
                        DIV(style='text-align:center;').html(
                            DIV(style='position:absolute;width:200px;height:200px;text-align:center;').html(
                                DIV(style='padding-top:20px;').html(
                                    STRONG(style='font-size:50px;').html('%.1f' % percent),
                                    SPAN(style='font-size:14px;font-weight:bold;').html('%')
                                ),
                                STRONG(style='font-size:16px;').html(addr),
                                rfreg,
                                STRONG().html(str(pat['total_alloc']) + ' '),
                                SMALL().html(V('counts'))
                            ),
                            Figure.Donut(pat['total_alloc'], total_free, width=200, height=200, hole=80, **Figure.THEME_UTIL),
                        )
                    )
                )
            )
                
        V.Page.html(
            Panel(**{'class' : 'panel-dgrey'}).Head(STRONG().html(V('%s Utilization') % domain_name)).Body(
                ROW().html(
                    COL(8).html(
                        HEAD(3, style='margin:0px;').html(V('System Utilization History')),
                        chart_hist
                    ),
                    COL(4).html(
                        HEAD(3, style='margin:0px;').html(V('System Current')),
                        chart_curr
                    )
                ),
                HEAD(3, style='margin:0px;').html(V('Counts')),
                ROW().html(
                    COL(2, style='padding:5px 0px 0px 0px;').html(HEAD(4, style='margin:0px;text-align:right;').html(V('Connections'))),
                    COL(10, style='padding:0px;').html(chart_conn)
                ),
                ROW().html(
                    COL(2, style='padding:5px 0px 0px 0px;').html(HEAD(4, style='margin:0px;text-align:right;').html(V('Translations'))),
                    COL(10, style='padding:0px;').html(chart_tran)
                ),
                HEAD(3, style='margin:0px;').html(V('NAT Status')),
                nat_table,
                HEAD(3, style='margin:0px;').html(V('PAT Status')),
                pool_list
            )
        )
    
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

@pageview(Manager)
def config(R, M, V):
    alert = None
    if R.Method == 'POST':
        if M.addDomain(R.Data['domain_name'], R.Data['ip'], R.Data['user'], R.Data['password']):
            alert = Alert(V('Connection Success'),
                          V('Setting %s with %s') % (R.Data['ip'], R.Data['domain_name']),
                          **{'class' : 'alert-success'})
        else:
            alert = Alert(V('Connection Failed'),
                          V('Incorrect Setting %s') % R.Data['domain_name'],
                          **{'class' : 'alert-danger'})
        
    elif R.Method == 'DELETE':
        if M.delDomain(R.Path[2]):
            alert = Alert(V('Disconnection Success'),
                          V('Erasing %s') % R.Path[2],
                          **{'class' : 'alert-success'})
        else:
            alert = Alert(V('Disconnection Failed'),
                          V('Incorrect Erasing %s') % R.Path[2],
                          **{'class' : 'alert-danger'})
    
    V.Menu.html(
        Modal(V('Register ASA Domain'), BUTTON(**{'class' : 'btn-primary', 'style' : 'float:right;'}).html(V('Connect ASA'))).html(
            Post('/asa/conf', V('Register'), **{'class' : 'btn-primary', 'style' : 'float:right;'}
            ).Text('domain_name', Post.TopLabel(V('ASA Domain Name')), placeholder=V('Unique Name Required')
            ).Text('ip', Post.TopLabel(V('ASA Address')), placeholder='XXX.XXX.XXX.XXX'
            ).Text('user', Post.TopLabel(V('Admin ID')), placeholder='admin'
            ).Password(label=Post.TopLabel(V('Password')))
        )
    )
    
    table = FooTable(V('Domain Name'), V('+ASA IP'), V('+Administrator ID'), V('+Start Connections'), V('+Max Connections'), '')
    
    for domain_name in M:
        table.Record(domain_name,
                     M[domain_name]['ip'],
                     M[domain_name]['user'],
                     M[domain_name]['conns'],
                     M[domain_name]['conn_max'],
                     DelButton('/asa/conf/' + domain_name, V('Delete'), tail=True, **{'class' : 'btn-xs'}))
    
    if alert != None: V.Page.html(alert)
    V.Page.html(table)