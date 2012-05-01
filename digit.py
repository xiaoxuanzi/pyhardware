#!/usr/bin/env python2.6
# coding: utf-8

import types

digs = list( 'KMGTPEZY' )
digName = { '1' : '' }
digValue = {}

val = 1
for d in digs:
    val = 1024 * val
    globals()[ d ] = val
    digName[ str( val ) ] = val
    digValue[ d ] = val
    digValue[ d + 'B' ] = val
    digValue[ d + 'IB' ] = val


def parse_int( i ):
    if i == '':
        return 0

    if type( i ) in ( type( 0 ), type( 0L ) ):
        return i
    elif type( i ) in types.StringTypes:

        i = i.upper().rstrip( 'B' ).rstrip( 'I' )

        unit = i[ -1 ]
        if unit in digs:
            if unit in digValue.keys():
                return int( float( i[ :-1 ] ) * digValue[ unit ] )
        else:
            return int( float( i ) )

    raise ValueError( 'Unrecognized int value:' + repr( i ) )

if __name__ == "__main__":
    print digValue
    print parse_int( '3MB' )
    print parse_int( '3M' )
    print parse_int( '3MiB' )
    print parse_int( '3' )
