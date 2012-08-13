#!/usr/bin/env python2.6
# coding: utf-8

import os


RAID_CARD = {
        'Serial Attached SCSI controller': [
                { 'brand': 'LSI Logic / Symbios Logic SAS2008 PCI-Express Fusion-MPT SAS-2 [Falcon] ', },
        ],

        'RAID bus controller': [
                { 'brand': '', },
        ],
}


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
              if is_raid_card( x ) ] ) > 1:
        raise MultiRAIDController( pciinfo )

    return pciinfo


def is_raid_card( pci ):

    if pci is None \
            or 'type' not in pci \
            or 'brand' not in pci:
        return False


    for condition in RAID_CARD.get( pci[ 'type' ], [] ):

        if 'brand' in condition:

            brand = condition[ 'brand' ]
            if pci[ 'brand' ].startswith( brand ):
                return True

    return False


def shellcmd( cmd ):
    return os.popen( cmd ).read()
