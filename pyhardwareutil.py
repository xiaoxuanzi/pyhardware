#!/usr/bin/env python2.6
# coding: utf-8

import os
import logging
import digit

logger = logging.Logger('_dumb_')
logger.setLevel( logging.CRITICAL )

def set_logger( lg ):
    global logger
    logger = lg

def shellcmd( cmd ):
    return os.popen( cmd ).read()

def read_file( fn ):
    with open( fn, 'r' ) as f:
        return f.read()

def parse_size( sz ):
    sz = sz.upper()
    sz = sz.split( ' ' )
    sz = [ x for x in sz if x != '' ]

    if sz[ 1 ][ 0 ] in digit.digs:
        sz = sz[ 0 ] + sz[ 1 ][ 0 ]
    else:
        sz = sz[ 0 ]

    return digit.parse_int( sz )
