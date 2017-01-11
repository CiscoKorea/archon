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

from service import *
from application.aci.models import EPTracker
#===============================================================================
# Create your views here.
#===============================================================================
@pageview(Manager)
def overview(R, M, V):
    
    cnt_nd = M.Node.count()
    cnt_tt = M.Tenant.count()
    cnt_bd = M.BridgeDomain.count()
    cnt_epg = M.EPG.count()
    cnt_ep = M.Endpoint.count()
    cnt_ft = M.Filter.count()
    cnt_ct = M.Contract.count()
    cnt_47d = M.Class('vnsCDev').count()
    cnt_47g = M.Class('vnsGraphInst').count()
    
    cnt_fc = M.Fault.list(severity='critical')
    cnt_fj = M.Fault.list(severity='major')
    cnt_fn = M.Fault.list(severity='minor')
    cnt_fw = M.Fault.list(severity='warning')
    
    def resolution(data, res):
        div = data / res
        return data, res * div, res * (div + 1)
    
    for domain_name in M:
        panel = Panel(**{'class' : 'panel-default'}).Head('%s %s' % (domain_name, V('Domain')))
        panel.Body(
            ROW().html(
                COL(1, 'md').html(Gauge('Node', *resolution(cnt_nd[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('Tenant', *resolution(cnt_tt[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('BD', *resolution(cnt_bd[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('EPG', *resolution(cnt_epg[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('EP', *resolution(cnt_ep[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('Filter', *resolution(cnt_ft[domain_name], 100), style='height:100px;')),
                
                COL(1, 'md').html(Gauge('Contract', *resolution(cnt_ct[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('L4/7Devices', *resolution(cnt_47d[domain_name], 100), style='height:100px;')),
                COL(1, 'md').html(Gauge('L4/7Graphs', *resolution(cnt_47g[domain_name], 100), style='height:100px;')),
                
#                 COL(1, 'md').html(' '),
                
                COL(3, 'md').html(
                    DIV(style='text-align:center;font-size:10px;font-weight:bold;color:#999;margin:0px;padding-top:6px;').html('Faults'),
                    ROW().html(
                        COL(3, style='padding-top:0px;').html(Gauge('critical', *resolution(len(cnt_fc[domain_name]), 100), style='height:70px;')),
                        COL(3, style='padding-top:0px;').html(Gauge('major', *resolution(len(cnt_fj[domain_name]), 100), style='height:70px;')),
                        COL(3, style='padding-top:0px;').html(Gauge('minor', *resolution(len(cnt_fn[domain_name]), 100), style='height:70px;')),
                        COL(3, style='padding-top:0px;').html(Gauge('warning', *resolution(len(cnt_fw[domain_name]), 100), style='height:70px;'))
                    )
                )
            )
        )
        V.Page.html(panel)
    
    health = M.getHealth()
    
    topo_hist = Line(height=295, min=0, max=100, *health['_tstamp'])
    node_hist = Line(height=145, min=0, max=100, *health['_tstamp'])
    epgs_hist = Line(height=200, min=0, max=100, *health['_tstamp'])
    
    node_cur = []
    epgs_cur = []
    
    dns = health.keys()
    
    for dn in dns:
        if dn == '_tstamp': continue
        elif '/epg-' in dn:
            name = re.sub('(uni/|tn-|ap-|epg-)', '', dn)
            epgs_hist.Data(name, *health[dn])
            epgs_cur.append((name, health[dn][-1]))
        elif '/node-' in dn:
            name = re.sub('(topology/|pod-|node-)', '', dn)
            node_hist.Data(name, *health[dn])
            node_cur.append((name, health[dn][-1]))
        elif '/' not in dn:
            topo_hist.Data(dn, *health[dn])
    
    node_cols = []
    node_vals = []
    epgs_cols = []
    epgs_vals = []
    node_cur = sorted(node_cur, key=lambda node: node[1])
    epgs_cur = sorted(epgs_cur, key=lambda node: node[1])
    for nc in node_cur: node_cols.append(nc[0]); node_vals.append(nc[1])
    for ec in epgs_cur: epgs_cols.append(ec[0]); epgs_vals.append(ec[1])
    
    node_now = HealthBar(height=145, xaxis=False, *node_cols).Data(V('Current Health'), *node_vals)
    epgs_now = HealthBar(height=200, xaxis=False, *epgs_cols).Data(V('Current Health'), *epgs_vals)
    
    V.Page.html(
        ROW().html(
            COL(6).html(
                Panel(**{'class' : 'panel-default'}).Head(V('Total Health')).Body(topo_hist)
            ),
            COL(6).html(
                Panel(**{'class' : 'panel-default'}).Head(V('Node Health')).Body(
                    node_hist,
                    node_now
                )
            )
        ),
        Panel(**{'class' : 'panel-default'}).Head(V('EPG Health')).Body(
            ROW().html(
                COL(6).html(epgs_hist),
                COL(6).html(epgs_now)
            )
        )
    )
    
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

@pageview(Manager)
def topoview(R, M, V):
    tns = M.Tenant.list()
    aps = M.AppProfile.list()
    epgs = M.EPG.list()
    
    pods = M.Pod.list()
    nodes = M.Node.list()
    
    nav = Navigation()
    
    for domain_name in M:
        topo = Topo(height=0)
        
        for tn in tns[domain_name]:
            set_topo(topo, tn['dn'], color='navy', path_color='black')
        
        for ap in aps[domain_name]:
            set_topo(topo, ap['dn'], color='blue')
        
        for pod in pods[domain_name]:
            set_topo(topo, pod['dn'], color='maroon', path_color='black')
            
        for node in nodes[domain_name]:
            set_topo(topo, node['dn'], color='orangered')
        
        for epg in epgs[domain_name]:
            set_topo(topo, epg['dn'], color='dodgerblue')
            paths = epg.Class('fvRsPathAtt').list()
            for path in paths:
                set_topo(topo, path['tDn'], color='indigo', path_color='orangered')
                topo.Edge(epg['dn'], path['tDn'])
        
        nav.Tab(domain_name, DIV(style='text-align:center;padding-top:10px;').html(topo))
    
    V.Page.html(nav)
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

@pageview(Manager)
def host(R, M, V):
    if R.Method == 'GET':
        if len(R.Path) > 3: host_one(R, M, V)
        else: host_all(R, M, V)

@pageview(Manager)
def device(R, M, V):
    if R.Method == 'GET':
        plen = len(R.Path)
        if plen > 4: device_one(R, M, V)
        elif plen > 3: device_all(R, M, V)
        else: device_all(R, M, V)
     
@pageview(Manager)
def tenant(R, M, V):
    if R.Method == 'GET':
        if len(R.Path) > 3: tenant_one(R, M, V)
        else: tenant_all(R, M, V)

@pageview(Manager)
def epg(R, M, V):
    if R.Method == 'GET':
        if len(R.Path) > 3: epg_one(R, M, V)
        else: epg_all(R, M, V)
    
@pageview(Manager)
def endpoint(R, M, V):
    if R.Method == 'GET':
        if len(R.Path) > 3: ep_one(R, M, V)
        else: ep_all(R, M, V)

@pageview(Manager)
def contract(R, M, V):
    if R.Method == 'GET':
        if len(R.Path) > 3: contract_one(R, M, V)
        else: contract_all(R, M, V)

@pageview(Manager)
def external(R, M, V):
    if R.Method == 'GET':
        if len(R.Path) > 3: external_one(R, M, V)
        else: external_all(R, M, V)

@pageview(Manager)
def fault(R, M, V):
    if R.Method == 'GET':
        plen = len(R.Path)
        if plen > 4: fault_one(R, M, V)
        elif plen > 3: fault_all(R, M, V)
        else: fault_all(R, M, V)

@pageview(Manager)
def epg_util(R, M, V):
    domain_name = None
    if len(R.Path) > 3: domain_name = R.Path[3]
    elif len(M) == 1: domain_name = M.keys()[0]
        
    if domain_name != None:
    #===========================================================================
    # Get Data
    #===========================================================================
        ctrl = M[domain_name]
        bytes = ctrl.get('/api/node/class/l2IngrBytesAgHist15min.json?query-target-filter=wcard(l2IngrBytesAg15min.dn,"uni/tn-.*/ap-.*/epg-.*/HDl2IngrBytesAg15min-0")')
        pkts = ctrl.get('/api/node/class/l2IngrPktsAgHist15min.json?query-target-filter=wcard(l2IngrPktsAg15min.dn,"uni/tn-.*/ap-.*/epg-.*/HDl2IngrPktsAg15min-0")')
        
    #===========================================================================
    # Logic
    #===========================================================================
        if bytes:
            table = DataTable(V('Name'), V('Unicast'), V('Multicast'))
            start = bytes[0]['l2IngrBytesAgHist15min']['attributes']['repIntvStart'][11:-13]
            end = bytes[0]['l2IngrBytesAgHist15min']['attributes']['repIntvEnd'][11:-13]
            tub = 0.00
            tmb = 0.00
            
            for data in bytes:
                b = data['l2IngrBytesAgHist15min']['attributes']
                dn = b['dn'].split('/HDl2IngrBytesAg15min')[0]
                raw = re.sub('(uni/|tn-|ap-|epg-)', '', dn).split('/')
                path_raw = '/'.join(raw[:2])
                name_raw = raw[2]
                name = PARA().html(SMALL().html(path_raw + '/')).html(Get('/aci/show/epgroup/%s/%s' % (domain_name, dn)).html(name_raw))
                ub = round(float(b['unicastRate']), 2)
                mb = round(float(b['multicastRate']), 2)
                tub += ub
                tmb += mb
                uni = str(ub) + ' Bytes'
                mlt = str(mb) + ' Bytes'
                for p in pkts:
                    if dn in p['l2IngrPktsAgHist15min']['attributes']['dn']:
                        uni += ' (' + str(round(float(p['l2IngrPktsAgHist15min']['attributes']['unicastRate']), 2)) + ' Packets)'
                        mlt += ' (' + str(round(float(p['l2IngrPktsAgHist15min']['attributes']['multicastRate']), 2)) + ' Packets)'
                        break;
                table.Record(name, uni, mlt)
            
    #===========================================================================
    # View
    #===========================================================================
            V.Page.html(HEAD(1).html('%s %s' % (domain_name, V('Domain'))))
            V.Page.html(
                ROW().html(
                    COL(6).html(CountPanel(V('Start'), 'hourglass-start', start, **{'class' : 'panel-dgrey'})),
                    COL(6).html(CountPanel(V('End'), 'hourglass-end', end, **{'class' : 'panel-dgrey'}))
                ),
                CountPanel(V('Total Unicast Bytes'), 'arrow-circle-o-right', tub, **{'class' : 'panel-dgrey'}),
                CountPanel(V('Total Multicast Bytes'), 'share-alt', tmb, **{'class' : 'panel-dgrey'})
            )
            V.Page.html(table)

        if not V.Page: V.Page.html(Alert(V('Info'), V('Non-exist APIC Connection'), **{'class' : 'alert-info'}))
    
    else:
        lg = ListGroup()
        for domain_name in M: lg.html(HEAD(3, **ATTR.click('/aci/stat/epgstat/%s' % domain_name)).html(domain_name))
        V.Page.html(lg)
    
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

@pageview(Manager)
def intf_util(R, M, V):
    domain_name = None
    node_dn = None
    if len(R.Path) > 3:
        domain_name = R.Path[3]
        node_dn = '/'.join(R.Path[4:]) 
        
    if node_dn != None:
        name = domain_name + re.sub('(topology|pod-|node-)', '', node_dn)
        node = M[domain_name](node_dn)
        intfs = node.System.PhysIf.list(sort='id')
        start = None
        end = None
        tib = 0.00
        teb = 0.00
        if intfs:
            table = DataTable(V('Name'), V('Ingress'), V('Egress'))
            for intf in intfs:
                intf_dn = intf['dn']
                try:
                    igr = M[domain_name](intf_dn + '/HDeqptIngrTotal15min-0', detail=True)
                    egr = M[domain_name](intf_dn + '/HDeqptEgrTotal15min-0', detail=True)
                except: continue 
                if start == None:
                    start = igr['repIntvStart'][11:-13]
                    end = igr['repIntvEnd'][11:-13]
                ibavg = round(float(igr['bytesRateAvg']), 2)
                iuavg = round(float(igr['utilAvg']), 2)
                ebavg = round(float(igr['bytesRateAvg']), 2)
                euavg = round(float(igr['utilAvg']), 2)
                tib += ibavg
                teb += ebavg
                
                igr_val = str(ibavg) + ' Bytes (' + str(iuavg) + ' %)'
                egr_val = str(ebavg) + ' Bytes (' + str(euavg) + ' %)'
                
                table.Record(intf['id'], igr_val, egr_val)
            
            V.Page.html(HEAD(1).html(name))
            V.Page.html(
                ROW().html(
                    COL(6).html(CountPanel(V('Start'), 'hourglass-start', start, **{'class' : 'panel-dgrey'})),
                    COL(6).html(CountPanel(V('End'), 'hourglass-end', end, **{'class' : 'panel-dgrey'}))
                ),
                CountPanel(V('Total Ingress Bytes'), 'download', tib, **{'class' : 'panel-dgrey'}),
                CountPanel(V('Total Egress Bytes'), 'upload', teb, **{'class' : 'panel-dgrey'})
            )
            V.Page.html(table)
    
    else:
        lg = ListGroup()
        for domain_name in M:
            nodes = M.Node.list(role='leaf', sort='dn', detail=True)
            for node in nodes[domain_name]:
                if node['fabricSt'] == 'active':
                    name = domain_name + re.sub('(topology|pod-|node-)', '', node['dn'])
                    lg.html(HEAD(3, **ATTR.click('/aci/stat/intfstat/%s/%s' % (domain_name, node['dn']))).html(name))
            nodes = M.Node.list(role='spine', sort='dn', detail=True)
            for node in nodes[domain_name]:
                if node['fabricSt'] == 'active':
                    name = domain_name + re.sub('(topology|pod-|node-)', '', node['dn'])
                    lg.html(HEAD(3, **ATTR.click('/aci/stat/intfstat/%s/%s' % (domain_name, node['dn']))).html(name))
        V.Page.html(lg)
    
    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))

@pageview(Manager)
def eptracker(R, M, V):
    if R.Method == 'GET' and len(R.Path) > 3 and R.Path[3] == 'init': M.initEndpoint()
    table = DataTable(V('Domain'), V('MAC'), V('IP'), V('EPG'), V('Interface'), V('Time Start'), V('Time Stop'))
    eps = EPTracker.objects.all()
    for ep in eps:
        epg = ep.tenant + '/' + ep.app + '/' + ep.epg
        intf = ' '
        for iname in ep.intf.split(','): intf += '<p><small>' + iname + '</small></p>'
        table.Record(ep.domain,
                     Get('/aci/show/endpoint/%s/%s' % (ep.domain, ep.dn)).html(ep.mac),
                     ep.ip,
                     '<small>' + epg + '</small>',
                     intf,
                     '<small>' + ep.start + '</small>',
                     '<small>' + ep.stop + '</small>')
    V.Page.html(table)
    V.Menu.html(
        BUTTON(**(ATTR.click('/aci/tool/eptracker') + {'class' : 'btn-primary'})).html(V('Refresh')),
        BUTTON(**(ATTR.click('/aci/tool/eptracker/init') + {'class' : 'btn-success'})).html(V('Reload'))
    )

@pageview(Manager)
def ofinder(R, M, V):
    if R.Method == 'GET' and len(R.Path) > 3:
        domain_name = R.Path[3]
        obj_name = '/'.join(R.Path[4:])
    elif R.Method == 'POST':
        domain_name = R.Data['domain_name']
        obj_name = R.Data['obj_name']
    else:
        domain_name = None
        obj_name = None
        
    V.Page.html(
        Post('/aci/tool/ofinder', V('Search'), **{'class' : 'btn-primary', 'style' : 'float:right;'}
        ).Text('domain_name', Post.TopLabel(V('APIC Domain Name')), placeholder=V('Unique Name Required')
        ).Text('obj_name', Post.TopLabel(V('Object Name')), placeholder=V('DN or Class Name'))
    )
    
    if domain_name != None:
        if '/' in obj_name:
            nav = Navigation()
            obj = M[domain_name](obj_name, detail=True)
            kv = KeyVal()
            for key in obj.attrs(): kv.Data(key, obj[key])
            nav.Tab(V('Details'), kv)
            
            try: parent = obj.parent(detail=True)
            except: pass
            else:
                kv = KeyVal()
                for key in parent.attrs(): kv.Data(key, parent[key] if key != 'dn' else Get('/aci/tool/ofinder/%s/%s' % (domain_name, parent[key])).html(parent[key]))
                nav.Tab(V('Parent Details'), kv)
            
            citems = {}
            children = obj.children(detail=True, sort='dn')
            for child in children:
                key = child.attrs()
                if child.class_name not in citems: citems[child.class_name] = FooTable(*['+' + k if k != 'dn' else V('DN') for k in key])
                citems[child.class_name].Record(*[child[k] if k != 'dn' else Get('/aci/tool/ofinder/%s/%s' % (domain_name, child[k])).html(child[k]) for k in key])
            
            cdiv = DIV()
            for class_name in citems: cdiv.html(citems[class_name])
            nav.Tab(V('Child Details'), cdiv)
            
            V.Page.html(
                HEAD(1).html(domain_name + '/' + obj_name),
                nav
            )
        else:
            objs = M[domain_name].Class(obj_name).list(detail=True)
            items = {}
            
            for obj in objs:
                key = obj.attrs()
                if obj.class_name not in items: items[obj.class_name] = FooTable(*['+' + k if k != 'dn' else V('DN') for k in key])
                items[obj.class_name].Record(*[obj[k] if k != 'dn' else Get('/aci/tool/ofinder/%s/%s' % (domain_name, obj[k])).html(obj[k]) for k in key])
            
            div = DIV()
            for class_name in items: div.html(items[class_name])
            V.Page.html(
                HEAD(1).html(domain_name + '/' + obj_name),
                div
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
        Modal(V('Register APIC Domain'), BUTTON(**{'class' : 'btn-primary', 'style' : 'float:right;'}).html(V('Connect APIC'))).html(
            Post('/aci/conf', V('Register'), **{'class' : 'btn-primary', 'style' : 'float:right;'}
            ).Text('domain_name', Post.TopLabel(V('APIC Domain Name')), placeholder=V('Unique Name Required')
            ).Text('ip', Post.TopLabel(V('APIC Address')), placeholder='XXX.XXX.XXX.XXX'
            ).Text('user', Post.TopLabel(V('Admin ID')), placeholder='admin'
            ).Password(label=Post.TopLabel(V('Password')))
        )
    )
    
    table = FooTable(V('Domain Name'), V('+APIC IP'), V('+Administrator ID'), V('+Start Connections'), V('+Max Connections'), '')
    
    for domain_name in M:
        table.Record(domain_name,
                     M[domain_name]['ip'],
                     M[domain_name]['user'],
                     M[domain_name]['conns'],
                     M[domain_name]['conn_max'],
                     DelButton('/aci/conf/' + domain_name, V('Delete'), tail=True, **{'class' : 'btn-xs'}))
    
    if alert != None: V.Page.html(alert)
    V.Page.html(table)





