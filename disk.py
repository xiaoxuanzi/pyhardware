#!/usr/bin/env python2.6
# coding: utf-8

import sys, os, os.path
import logging
import types

import digit
import hardware

class DiskError( Exception ): pass
class NoSuchDevice( DiskError ): pass
class UnrecognizedDevice( DiskError ): pass

class Unsupported( DiskError ): pass
class Duplicated( DiskError ): pass
class PathError( DiskError ): pass

class MultiRAIDController( Unsupported ): pass
class UnsupportedDevice( Unsupported ): pass
class UnspportedInquiry( Unsupported ): pass
class UnspportedVirtualDiskID( Unsupported ): pass

class DuplicatedVirtualDisk( Duplicated ): pass

class NotMountPoint( PathError ): pass


logger = logging.Logger('_dumb_')
logger.setLevel( logging.CRITICAL )

def set_logger( lg ):
    global logger
    logger = lg

megacli = None # would be filled in by pyhardwareconf.py

PRODUCTS = {
        'SEAGATE': {
                'ST31000424SS' : { 'capacity' : "1T", 'interface': 'SAS', 'bandwidth':'6Gbps', 'spinSpeed':7200, 'mediaType': 'ATA' },
                'ST9146803SS' : { 'capacity' : "146G", 'interface': 'SAS', 'bandwidth':'6Gbps', 'spinSpeed':10000, 'mediaType': 'SAS' },
                'ST9146802SS'  : { 'capacity' : "146G", 'interface': 'SAS', 'bandwidth':'3Gbps', 'spinSpeed':10000, 'mediaType': 'SAS' },
                'ST3146807LC'  : { 'capacity' : "146G", 'interface': 'SCSI', 'bandwidth':'6Gbps', 'spinSpeed':10000, 'mediaType': 'SAS' },
                'ST32000644NS' : { 'capacity' : "2T", 'interface': 'SATA', 'bandwidth':'3Gbps', 'spinSpeed':7200, 'mediaType': 'ATA' },
        },
        # NOTE: This actually is SEAGATE disk, but MegaCli report its vendor as 'ATA'
        'ATA': {
                'ST32000644NS' : { 'capacity' : "2T", 'interface': 'SATA', 'bandwidth':'3Gbps', 'spinSpeed':7200, 'mediaType': 'ATA' },
        },
        'TOYOU': {
                'NetStor_iSUM520' : { 'capacity' : "-", 'interface': '-', 'bandwidth':'4Gbps', 'spinSpeed':0, 'mediaType': 'ARR' },
        },
        'IBM': {
                'IC35L146UCDY10-0' : { 'capacity' : "146G", 'interface': 'SCSI', 'bandwidth':'-', 'spinSpeed':10000, 'mediaType': 'SAS' },
        },
        'HUAWEI': {
                'S2600' : { 'capacity' : "-", 'interface': '-', 'bandwidth':'-', 'spinSpeed':0, 'mediaType': 'ARR' },
        },
        'LSILOGIC': {
                'Logical Volume' : { 'capacity' : "-", 'interface': '-', 'bandwidth':'-', 'spinSpeed':0, 'mediaType': 'UNKNOWN' },
        },


}

def ensure_mountpoint( path ):
    if not os.path.ismount( path ):
        raise NotMountPoint( path )

def get_mountpoint( path ):

    path = os.path.realpath( path )

    while not os.path.ismount(path):
        path = os.path.dirname(path)

    return path

def get_device( path ):
    mp = get_mountpoint( path )

    # TODO use mtab
    dev = shellcmd( '/bin/mount | /bin/grep "on %s "' % ( mp,  ) ).split( ' ' )[0]
    return dev

def get_dev_uuid( devpath ):

    devuuids = shellcmd( '/sbin/blkid %s | /bin/grep -o "UUID[^ ]*"' % ( devpath,  ) )
    devuuids = devuuids.strip().split( '\n' )
    devuuids = [ x.strip().split( '"' )[ 1 ] for x in devuuids ]
    return devuuids[ 0 ]

def get_mtab():
    mtab = read_file( '/etc/mtab' )
    lines = mtab.strip().split( '\n' )
    lines = [ x.strip().split( ' ' ) for x in lines ]

    return lines


def get_dev_fs( devpath ):
    lines = get_mtab()

    lines = [ x for x in lines if x[ 0 ] == devpath ]

    if len( lines ) == 0:
        return 'unknown'
    else:
        return lines[ 0 ][ 2 ]

def get_data_dirs():

    folders = os.listdir( '/' )

    folders = [ '/' + x for x in folders
                if x.startswith( 'data' ) ]

    folders = [ x for x in folders
                if get_mountpoint( x ) == x ]

    return folders

def get_devicepath_table():

    # os.readlink('/dev/disk/by-path/pci-0000:05:06.0-scsi-0:0:0:0-part7')

    busdir = '/dev/disk/by-path'
    devicepaths = os.listdir( busdir )

    devmap = {}
    for devpath in devicepaths:
        dev = os.readlink( os.path.join( busdir, devpath ) )
        dev = os.path.normpath( os.path.join( busdir, dev ) )
        devmap[ dev ] = devpath

    return devmap

def get_dev_buspath( dev ):
    m = get_devicepath_table()
    try:
        return m[ dev ]
    except KeyError, e:
        raise NoSuchDevice( dev )

def parse_size( sz ):
    sz = sz.upper()
    sz = sz.split( ' ' )
    sz = [ x for x in sz if x != '' ]
    if sz[ 1 ][ 0 ] in ( 'M', 'K', 'G', 'T' ):
        sz = sz[ 0 ] + sz[ 1 ][ 0 ]
    else:
        sz = sz[ 0 ]

    return digit.parse_int( sz )



def get_raid_info():

    # Virtual Disk: 2 (target id: 1)
    # Virtual Drive: 2    // another syntax
    # RAID Level: Primary-5, Secondary-0, RAID Level Qualifier-3
    # Size:5273600MB
    # State: Optimal
    # Stripe Size: 64kB
    # Current Cache Policy: WriteBack ReadAdaptive Direct
    # Device Id: 0
    # Media Error Count: 0
    # Raw Size: 953869MB [0x74706db0 Sectors]
    # Non Coerced Size: 953357MB [0x74606db0 Sectors]
    # Coerced Size: 953344MB [0x74600000 Sectors]
    # Inquiry Data: SEAGATE ST31000424SS    KS659WK0Z3RZ
    # Device Id: 1
    # Raw Size: 953869MB [0x74706db0 Sectors]
    # Non Coerced Size: 953357MB [0x74606db0 Sectors]
    # Coerced Size: 953344MB [0x74600000 Sectors]
    # Inquiry Data: SEAGATE ST31000424SS    KS659WK0Z34P
    # Device Id: 2

    cmd = megacli + ' -LdPdInfo  -aAll | grep "Device Id: \|Inquiry Data: \|Virtual Disk: \|Virtual Drive: \|RAID Level *: \|Media Error Count:\|Size:\|State: \|Current Cache Policy: "'

    megalines = shellcmd( cmd ).strip().split( "\n" )
    megalines = [ x for x in megalines if x != '' ]

    vds = {}
    vd = None
    pds = {}
    pd = None

    for line in megalines:

        elts = line.strip().split(':', 1)
        elts = [ x.strip() for x in elts ]

        ( k, v ) = elts
        if k == 'Virtual Disk' \
                or k == 'Virtual Drive':
            # Virtual Disk: 10 (target id: 10)

            vs = v.split( ' ', 1 )

            if len( vs ) == 1:
                raise UnspportedVirtualDiskID( v )

            targetid = vs[ 1 ].split( ' ' )[ -1 ][ :-1 ]
            try:
                int( targetid )
            except Exception, e:
                raise UnspportedVirtualDiskID( v, targetid )

            vd = { 'id' : int( targetid ), 'physicalDisks':{} }

            if vds.has_key( targetid ):
                raise DuplicatedVirtualDisk( targetid )

            vds[ targetid ] = vd

        elif k.startswith( 'RAID Level' ):
            vd[ 'level' ] = [ int( x.strip()[ -1 ] )
                              for x in v.split( ',' )[ :2 ] ]
        elif k == 'Size':
            # vd[ 'size' ] = int( v[ :-2 ] ) * 1024 * 1024
            vd[ 'size' ] = parse_size( v )

        elif k == 'State':
            vd[ 'state' ] = v

        elif k == 'Current Cache Policy':
            vd[ 'policy' ] = v

        elif k == 'Device Id':
            pd = { 'id' : int( v ) }
            pds[ v ] = pd
            vd[ 'physicalDisks' ][ v ] = pd

        elif k == 'Media Error Count':
            pd[ 'mediaError' ] = int( v )

        elif k == 'Coerced Size':
            pd[ 'size' ] = parse_size( v )

        elif k == 'Inquiry Data':
            info = [ x.strip() for x in v.split( ' ' ) if x != '' ]

            # IBM-ESXSCBRCA146C3ETS0 write vender and model together

            if len( info ) == 2 and info[ 0 ].startswith( 'IBM' ):
                pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = info[ 0 ].split( '-', 1 ) + info[ 1: ]

            elif len( info ) == 4:
                if info[ 0 ] == 'ATA':
                    # Like this:
                    # Inquiry Data: ATA     ST32000644NS    BB28            9WM575H9
                    pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = [ 'SEAGATE',  ] + [ info[ 1 ], info[ 3 ] ]
                else:
                    raise UnspportedInquiry( v )
            else:
                pd[ 'vendor' ], pd[ 'model' ], pd[ 'serial' ] = info

    return ( vds, pds )

def get_dev_physical( dev, phyenv = {} ):
    return get_dev_physical_stack( dev, phyenv )[ 0 ]

def _get_dev_physical_path( dev ):

    blockroot = '/sys/block/'

    if dev.startswith( '/dev/cciss/c' ):

        # /dev/cciss/c0d0p1

        phydev = dev.strip( '0123456789' )[ :-1 ].split( '/' )[ -1 ]
        blockDevPath = blockroot + 'cciss!' +  phydev


    elif dev.startswith( '/dev/sd' ):

        # /dev/sda1

        phydev = dev.strip( '0123456789' ).split( '/' )[ 2 ]
        blockDevPath = blockroot + phydev

    else:
        raise UnsupportedDevice( dev )


    if not os.path.isdir( blockDevPath ):
        raise UnrecognizedDevice( dev, blockDevPath )

    phyPath = os.path.realpath(
            os.path.join( blockDevPath, 'device' ) )

    return phyPath

def get_dev_physical_stack( dev, phyenv = {} ):

    # NOTE: linux only

    phyenv[ 'pciinfo' ] = phyenv.get( 'pciinfo', hardware.get_pci_info() )
    rst = []


    node = _get_dev_physical_path( dev )
    while node != '/':

        phyinfo = collect_physical_device_info( node, phyenv[ 'pciinfo' ] )

        if phyinfo.has_key( 'subsystem' ):
            rst += [ phyinfo ]

        node = os.path.split( node )[ 0 ]


    if len( rst ) > 0:

        _collect_raid_info( rst, phyenv )
        d = rst[ 0 ]
        d[ 'mediaType' ] = determine_media_type( d )


    return rst

def _collect_raid_info( phyStack, phyenv = {} ):

    isRaidCtr = lambda x: x.get( 'pciinfo', {} ).get( 'type' ) in [ hardware.KEY_RAID_CONTROLLER ]

    raidctrs = [ x for x in phyStack if isRaidCtr( x ) ]

    if raidctrs == [] \
            or phyStack[ 0 ] == raidctrs[ 0 ]:
        # cciss RAID controller has no children device as disk
        return

    raidctr = raidctrs[ 0 ]


    topDev = phyStack[ 0 ]

    if topDev.get( 'subsystem' ) != 'scsi':
        # The top device is not a [physical/logical] scsi device. dont know how to
        # handle it yet
        return


    phyenv[ 'raidinfo' ] = phyenv.get( 'raidinfo', get_raid_info() )

    ( vds, pds ) = phyenv[ 'raidinfo' ]


    _id = topDev[ 'id' ].split( ':' )[ 2 ]
    topDev[ 'raid' ] = { 'virtualDisk' : vds[ _id ], }

def determine_media_type( d ):

    if d.has_key( 'raid' ):

        raid = d[ 'raid' ]

        vd = raid[ 'virtualDisk' ]
        pds = vd[ 'physicalDisks' ]

        if len( pds.keys() ) > 1:
            # traditional RAID 5/6
            tp = 'HDD'
        else:
            pd = pds.values()[ 0 ]
            try:
                tp = PRODUCTS[ pd[ 'vendor' ] ][ pd[ 'model' ] ][ 'mediaType' ]
            except Exception, e:
                logger.warn( 'Unknown physical device as RAID 0:' + repr( pd ) )
                tp = 'UNKNOWN'

        return tp

    else:

        # cciss RAID controller has no children device as disk
        if d.get( 'subsystem' ) == 'scsi':

            try:
                tp = PRODUCTS[ d[ 'vendor' ] ][ d[ 'model' ] ][ 'mediaType' ]
            except Exception, e:
                logger.warn( 'Unknown physical device:' + repr( d ) )
                tp = 'UNKNOWN'
        else:
            tp = 'UNKNOWN'

        return tp

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

def shellcmd( cmd ):
    return os.popen( cmd ).read()

def read_file( fn ):
    with open( fn, 'r' ) as f:
        return f.read()


try:
    import pyhardwareconf
    megacli = pyhardwareconf.megacli
except Exception, e:
    pass

if __name__ == "__main__":
    import pprint
    args = sys.argv

    if len( args ) > 1:
        if args[ 1:2 ] == [ 'test' ]:
            pprint.pprint( get_dev_physical_stack( '/dev/sdb' ) )
        elif args[ 1:2 ] == [ 'raid' ]:
            pprint.pprint( get_raid_info() )
