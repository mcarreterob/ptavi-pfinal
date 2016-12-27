#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os

try:
    config = sys.argv[1]
except IndexError:
    sys.exit('Usage: python uaserver.py config')


class XMLHandler(ContentHandler):

    def __init__(self):
        """Inicializador de varibles. config_dic es un diccionario en el que
            se guardaran los datos de cada etiqueta. data_list es una lista
            donde se guardaran todos los diccionarios"""
        self.config_dic = {}
        self.data_list = []

    def startElement(self, name, attrs):
        if name == 'account':
            self.config_dic['username'] = attrs.get('username', '--')
            self.config_dic['passwd'] = attrs.get('passwd', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'uaserver':
            self.config_dic['uas_ip'] = attrs.get('ip', '--')
            self.config_dic['uas_port'] = attrs.get('puerto', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'rtpaudio':
            self.config_dic['rtp_port'] = attrs.get('puerto', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'regproxy':
            self.config_dic['reg_ip'] = attrs.get('ip', '--')
            self.config_dic['reg_port'] = attrs.get('puerto', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'log':
            self.config_dic['log_path'] =  attrs.get('path', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'audio':
            self.config_dic['audio_path'] = attrs.get('path', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}

    def get_data(self):
        return self.data_list

parser = make_parser()
XMLH = XMLHandler()
parser.setContentHandler(XMLH)
parser.parse(open(config))
data_list = XMLH.get_data()
# Variables del config xml
username = data_list[0]['username']
password = data_list[0]['passwd']
uas_ip = data_list[1]['uas_ip']
uas_port = data_list[1]['uas_port']
rtp_port = data_list[2]['rtp_port']
regproxy_IP = data_list[3]['reg_ip']
regproxy_port = data_list[3]['reg_port']
log_file = data_list[4]['log_path']
audio_file = data_list[5]['audio_path']


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    rtp_list = []

    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read().decode('utf-8')
            print("El cliente nos manda " + line)
            line_slices = line.split()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            metodo = line_slices[0]
            if metodo == 'INVITE':
                self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                self.wfile.write(b'SIP/2.0 180 Ring\r\n\r\n')
                self.wfile.write(b'SIP/2.0 200 OK\r\n')
                peticion = 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' + \
                           'o=' + username + ' ' + uas_ip + '\r\n' + 's=misesion\r\n' + \
                           't=0\r\n' + 'm=audio ' + rtp_port + ' RTP\r\n'
                self.wfile.write(bytes(peticion, 'utf-8'))
                self.rtp_user = line_slices[6].split('=')[1]
                self.rtp_list.append(self.rtp_user)
                self.rtp_ip = line_slices[7]
                self.rtp_list.append(self.rtp_ip)
                self.rtp_port = line_slices[11]
                self.rtp_list.append(self.rtp_port)
            elif metodo == 'ACK':
                print('me esta llegando ', line)
                peticion = 'ACK sip:' + self.rtp_list[0] + ' SIP/2.0'
                self.wfile.write(bytes(peticion, 'utf-8'))
                aEjecutar = 'mp32rtp -i ' + self.rtp_list[1] + ' -p '
                aEjecutar += self.rtp_list[2] + ' < ' + audio_file
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
                print('Finished transfer')
            elif metodo == 'BYE':
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            elif metodo != 'INVITE' or metodo != 'BYE' or metodo != 'ACK':
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad Request')

# Creamos servidor y escuchamos
serv = socketserver.UDPServer((uas_ip, int(uas_port)), EchoHandler)
print("Listening...")
serv.serve_forever()
