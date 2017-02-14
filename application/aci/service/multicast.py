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

#specific domain which using multicast 
MCAST_DOMAIN = ['dc_fabric']

def multicast_all(R, M, V):
    #===========================================================================
    # Get Data
    #===========================================================================
    # pimRoute_data = M.Class('pimRoute').list(detail=True, sort=['grp', 'src'])
    #===========================================================================
    # Logic
    #===========================================================================
    table = DataTable(V('Group_Address'), V('Source'), V('HWByteCnt'), V('Interface'), V('Assert Metric'))

    for domain_name in M:
        if domain_name not in MCAST_DOMAIN:
            continue
        pimRoute_data = M[domain_name].Class('pimRoute').list(detail=True, sort=['grp', 'src'])
        stats = {}
        hw_byte_cnt = 0
        for route in pimRoute_data:
            grp_key = route['grp']
            src_key = route['src']
            hw_byte_cnt = int(route['hwByteCnt']) if route.has_key('hwByteCnt') else 0
            if stats.has_key( grp_key):
                if stats[grp_key].has_key( src_key):
                    stats[grp_key][src_key]['hwByteCnt'] = int(stats[grp_key][src_key]['hwByteCnt']) + hw_byte_cnt
                else:
                    stats[grp_key][src_key] = {}
                    stats[grp_key][src_key]['hwByteCnt'] = hw_byte_cnt
            else:
                stats[grp_key] = {}
                stats[grp_key][src_key] = {}
                stats[grp_key][src_key]['hwByteCnt'] = hw_byte_cnt
                stats[grp_key][src_key]['interface'] = route['iif']
                stats[grp_key][src_key]['assertMetric'] = route['assertMetric']

        for grp in stats.keys():
            for src in stats[grp].keys():
                if stats[grp][src].has_key('interface') and stats[grp][src].has_key('assertMetric') :
                    table.Record(grp, src, stats[grp][src]['hwByteCnt'], stats[grp][src]['interface'], stats[grp][src]['assertMetric'])

        #===========================================================================
        # View
        #===========================================================================
        V.Page.html(HEAD(1).html('%s %s' % (domain_name, V('Domain'))))
        V.Page.html(table)

    V.Menu.html(BUTTON(**(ATTR.click('/'.join(R.Path)) + {'class' : 'btn-primary'})).html(V('Refresh')))



def multicast_one(R, M, V):
    pass
