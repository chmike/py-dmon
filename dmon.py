from __future__ import print_function
# -*- coding: utf-8 -*-

from threading import Thread, Lock, Condition
from datetime import datetime
import socket
import struct
import select
import atexit
import time
import json
import sys
import ssl
import io

ackCode = 0xA5

class Message:
    stamp = datetime.utcnow()
    level = "info"
    system = "dmon"
    component = "test"
    message = "no problem"

    def jsonEncode(self): 
        m = dict()
        m['stamp'] = self.stamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        m['level'] = self.level
        m['system'] = self.system
        m['component'] = self.component
        m['message'] = self.message
        jmsg = json.dumps(m, skipkeys=True)
        bmsg = io.BytesIO()
        bmsg.write(bytearray([ord('D'),ord('M'),ord('O'),ord('N')]))
        bmsg.write(struct.pack("<I", len(jmsg)))
        bmsg.write(jmsg.encode('utf-8'))
        return bmsg.getvalue()

    def binaryEncode(self):
        bmsg = io.BytesIO()
        bmsg.write(bytearray([ord('D'),ord('M'),ord('O'),ord('N'), 0,0,0,0,15,1]))
        sec = (self.stamp - datetime(1970,1,1)).total_seconds()
        bmsg.write(struct.pack(">q", int(sec)))
        bmsg.write(struct.pack(">I", int((sec*1e6)%1e6)*1000))
        bmsg.write(bytearray([0,0]))
        bmsg.write(struct.pack("<I",len(self.level)))
        bmsg.write(self.level)
        bmsg.write(struct.pack("<I",len(self.system)))
        bmsg.write(self.system)
        bmsg.write(struct.pack("<I",len(self.component)))
        bmsg.write(self.component)
        bmsg.write(struct.pack("<I",len(self.message)))
        bmsg.write(self.message)
        msgLen = len(bmsg.getvalue())
        bmsg.seek(4,0)
        bmsg.write(struct.pack("<I",msgLen-8))
        return bmsg.getvalue()

class Client:
    def __init__(self, address, json, useTLS):
        self.__json = json
        self.__useTLS = useTLS
        self.buf = bytearray(1)
        self.hostname, self.port = address.split(":")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.hostIP = socket.gethostbyname(self.hostname)
        except:
            raise IOError("unknown host name: " + self.hostname)

    def send(self, msg):
        if not isinstance(msg, Message): 
            raise IOError("dmon.Client: msg is not of type Message")
        if self.__json:
            data = msg.jsonEncode()
        else:
            data = msg.binaryEncode()
        if not self.__send(data) and (not self.__connect() or not self.__send(data)):
            return False

        # get acknowledgment
        try:
            n = self.sock.recv_into(self.buf)
        except:
            return False
        # self.sock.close()
        if n == 0 or self.buf != ackCode:
            return False
        return True

    def __connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.__useTLS:
            #certReq = ssl.CERT_NONE
            certReq = ssl.CERT_REQUIRED
            self.sock = ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_TLS, keyfile="pki/client.key", 
                certfile="pki/client.crt", cert_reqs=certReq, ca_certs="pki/rootCA.crt", ciphers="ADH-AES256-SHA256:ALL")
        try:
            self.sock.connect((self.hostIP, int(self.port)))
        except:
            return False
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(30)
        return True


    def __send(self, data):
        try:
            self.sock.send(data)
        except:
            return False
        return True
