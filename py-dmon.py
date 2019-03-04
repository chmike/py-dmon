#!/usr/bin/env python2
from __future__ import print_function
# -*- coding: utf-8 -*-

import sys
import argparse
import dmon
from datetime import datetime
import traceback

def runAsServer(args):
    print("run as server, listening on ", args.address)
    print( "not implemented")

def runAsClient(args):
    print("target:", args.address)

    client = dmon.Client(args.address, args.json, args.useTLS)
    m = dmon.Message()
    while (1):
        m.stamp = datetime.utcnow()
        client.send(m)


if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='py-dmon client server')
    parser.add_argument('-a', dest='address', action='store', default="127.0.0.1:3000",
                    help='address to listen (server), or send message to (client) (default "127.0.0.1:3000")')
    parser.add_argument('-s', dest='server', action='store_true', help='run as server')
    parser.add_argument('-c', dest='server', action='store_false', help='run as client')
    parser.add_argument('-json', dest='json', action='store_true', help="use json encoding (default binary)")
    parser.add_argument('-tls', dest='useTLS', action='store_true', help="use TLS (default tcp)")
    args = parser.parse_args()
    print("args:", args)
    try:
        if args.server:
            runAsServer(args)
        else:
            runAsClient(args)
    except:
        print("Unexpected error:", sys.exc_info())
        print(traceback.format_exc())

