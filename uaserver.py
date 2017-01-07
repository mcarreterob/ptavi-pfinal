#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os
import time

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

def makeLog(log_file, hora, evento_log):
    fichero = open(log_file, 'a')
    hora = time.gmtime(time.time())
    fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
    evento_log = evento_log.replace('\r\n', ' ')
    fichero.write(evento_log + '\r\n')
    fichero.close()


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
                evento_log = ' Received from ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + line
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                peticion = 'SIP/2.0 100 Trying\r\n\r\n'
                peticion += 'SIP/2.0 180 Ring\r\n\r\n'
                peticion += 'SIP/2.0 200 OK\r\n\r\n'
                peticion += 'Content-Type: application/sdp\r\n\r\n' + \
                           'v=0\r\n' + 'o=' + username + ' ' + uas_ip + \
                           '\r\n' + 's=misesion\r\n' + 't=0\r\n' + \
                           'm=audio ' + rtp_port + ' RTP\r\n\r\n'
                evento_log = ' Sent to ' + regproxy_IP + ':' + \
                             regproxy_port + ': ' + peticion
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                self.wfile.write(bytes(peticion, 'utf-8'))
                self.rtp_user = line_slices[6].split('=')[1]
                self.rtp_list.append(self.rtp_user)
                self.rtp_ip = line_slices[7]
                self.rtp_list.append(self.rtp_ip)
                self.rtp_port = line_slices[11]
                self.rtp_list.append(self.rtp_port)
            elif metodo == 'ACK':
                print('me esta llegando ', line)
                evento_log = ' Received from ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + line
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                #vlc = 'cvlc rtp://@' + self.rtp_list[1] + ':' + \
                #        self.rtp_list[2] + ' 2> /dev/null'
                #print('Vamos a ejecutar', vlc)
                #os.system(vlc)
                aEjecutar = './mp32rtp -i ' + self.rtp_list[1] + ' -p '
                aEjecutar += self.rtp_list[2] + ' < ' + audio_file
                evento_log = ' Sending to ' + self.rtp_list[1] + ':' + \
                              self.rtp_list[2] + ': ' + 'audio_file'
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
                print('Finished transfer')
                evento_log = ' Finished audio transfer to ' + \
                             self.rtp_list[1] + ':' + self.rtp_list[2] + \
                             ': ' + 'audio_file'
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
            elif metodo == 'BYE':
                evento_log = ' Received from ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + line
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                peticion = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(bytes(peticion, 'utf-8'))
                evento_log = ' Sent to ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + peticion
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
            elif metodo != 'INVITE' or metodo != 'BYE' or metodo != 'ACK':
                evento_log = ' Received from ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + line
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                peticion = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(byes(peticion, 'utf-8'))
                evento_log = ' Sent to ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + peticion
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
            else:
                evento_log = ' Received from ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + line
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)
                peticion = 'SIP/2.0 400 Bad Request'
                self.wfile.write(bytes(peticion, 'utf-8'))
                evento_log = ' Sent to ' + regproxy_IP + ':' + \
                              regproxy_port + ': ' + peticion
                hora = time.gmtime(time.time())
                makeLog(log_file, hora, evento_log)

# Creamos servidor y escuchamos
# START_LOG
evento_log = ' Starting uaserver...'
hora = time.gmtime(time.time())
makeLog(log_file, hora, evento_log)
# END_LOG
try:
    serv = socketserver.UDPServer((uas_ip, int(uas_port)), EchoHandler)
    print("Listening...")
    serv.serve_forever()
except KeyboardInterrupt:
    evento_log = ' Finishing uaserver.'
    hora = time.gmtime(time.time())
    makeLog(log_file, hora, evento_log)
    sys.exit('\r\nFinished uaserver')
