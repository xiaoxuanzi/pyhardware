#!/usr/bin/env python2.6
# coding: utf-8

import os

from pyhardwareutil import *

vgdisplay = 'vgdisplay'

try:
    import pyhardwareconf
    vgdisplay = pyhardwareconf.vgdisplay
except Exception, e:
    pass

def lvm_info():
    cmd = vgdisplay + ' -v'

    vglines = shellcmd( cmd ).strip().split( "\n" )
    vglines = [ x for x in vglines if x != '' ]

    vgs = {}
    vg = None

    lvs = None
    lv = None

    pvs = None
    pv = None


    for line in vglines:

        elts = line.strip().split(' ')
        elts = [ x.strip()
                 for x in elts
                 if x != '' ]

        if elts[ 0:2 ] == [ 'VG', 'Name' ]:
            name = elts[ 2 ]
            if not vgs.has_key( name ):
                vgs[ name ] = { 'name' : name, 'logicalVolumns' : {}, 'physicalVolumns' : {} }
                vg = vgs[ name ]
                lvs = vg[ 'logicalVolumns' ]
                pvs = vg[ 'physicalVolumns' ]

        elif elts[ 0:2 ] == [ 'LV', 'Name' ]:
            name = elts[ 2 ]
            if os.path.islink( name ):
                mapper = os.readlink( name )
            lvs[ name ] = { 'name': name, 'mapper': mapper }
            lv = lvs[ name ]

        elif elts[ 0:2 ] == [ 'LV', 'Size' ]:
            lv[ 'size' ] = parse_size( ' '.join( elts[ 2: ] ) )

        elif elts[ 0:2 ] == [ 'PV', 'Name' ]:
            name = elts[ 2 ]
            pvs[ name ] = { 'name' : name, 'dev' : name }


    return vgs
