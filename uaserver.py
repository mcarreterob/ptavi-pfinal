#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

try:
    config = sys.argv[1]
except IndexError:
    sys.exit('Usage: python uaclient.py config method option')

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
log_path = data_list[4]['log_path']
audio_path = data_list[5]['audio_path']

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((regproxy_IP, int(regproxy_port)))

