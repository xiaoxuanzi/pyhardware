#!/usr/bin/env python2.6
# coding: utf-8

import os


KEY_RAID_CONTROLLER = 'RAID bus controller'


class HardwareError( Exception ): pass

class Unsupported( HardwareError ): pass

class MultiRAIDController( Unsupported ): pass




def get_pci_info():
    pciinfo = shellcmd( '/sbin/lspci' ).strip().split( "\n" )
    pciinfo = [ x.strip().split( ' ', 1 ) for x in pciinfo ]

    for x in pciinfo:
        e = x[ 1 ].split( ':', 1 )
        x[ 1 ] = { 'type': e[ 0 ].strip(),
                   'brand':e[ 1 ].strip() }

    pciinfo = dict( pciinfo )

    if len( [ x for x in pciinfo.values()
              if x[ 'type' ] == KEY_RAID_CONTROLLER ] ) > 1:
        raise MultiRAIDController( pciinfo )

    return pciinfo

def shellcmd( cmd ):
    return os.popen( cmd ).read()
