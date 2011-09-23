#!/usr/bin/env python2.6
# coding: utf-8

import os

from pyhardwareutil import *

def device_bus_stack( node, phyenv ):

    rst = []
    while node != '/':

        phyinfo = collect_physical_device_info( node, phyenv[ 'pciinfo' ] )

        if phyinfo.has_key( 'subsystem' ):
            rst += [ phyinfo ]

        node = os.path.split( node )[ 0 ]

    return rst


def collect_physical_device_info( node, pciinfo ):

    phyinfo = {}

    phyinfo[ 'id' ] = os.path.split( node )[ -1 ]

    _link_tail( node, 'subsystem', phyinfo )
    _link_tail( node, 'bus', phyinfo )
    _link_tail( node, 'driver', phyinfo )

    _file_cont( node, 'vendor', phyinfo )
    _file_cont( node, 'model', phyinfo )
    _file_cont( node, 'rev', phyinfo )


    pref = '0000:'

    if phyinfo.get( 'subsystem' ) == 'pci' \
            and phyinfo[ 'id' ].startswith( pref ):

        # A real pci device

        pcikey = phyinfo[ 'id' ][ len( pref ): ]

        if pciinfo.has_key( pcikey ):
            phyinfo[ 'pciinfo' ] = pciinfo[ pcikey ]

    return phyinfo

def _file_cont( path, key, rst ):

    contpath = os.path.join( path, key )

    if os.path.isfile( contpath ):
        rst[ key ] = read_file( contpath ).strip()
        return rst[ key ]

def _link_tail( path, key, rst ):

    linkpath = os.path.join( path, key )

    if os.path.islink( linkpath ):
        rst[ key ] = os.readlink( linkpath ).split( os.path.sep )[ -1 ]
        return rst[ key ]
