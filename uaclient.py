#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import hashlib
import os
import time

try:
    config = sys.argv[1]
    metodo = sys.argv[2]
    opcion = sys.argv[3]
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
log_file = data_list[4]['log_path']
audio_file = data_list[5]['audio_path']

def makeLog(log_file, hora, evento_log):
    fichero = open(log_file, 'a')
    hora = time.gmtime(time.time())
    fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
    evento_log = evento_log.replace('\r\n', ' ')
    fichero.write(evento_log + '\r\n')
    fichero.close()

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((regproxy_IP, int(regproxy_port)))

# START_LOG
evento_log = ' Starting uaclient...'
hora = time.gmtime(time.time())
makeLog(log_file, hora, evento_log)
# END_LOG

if metodo == 'REGISTER':
    try:
        peticion = 'REGISTER sip:' + username + ':' + uas_port + \
                   ' SIP/2.0\r\n' + 'Expires: ' + opcion + '\r\n'
        print('Enviando: ' + peticion)
        my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
        # START_LOG
        evento_log = ' Sent to ' + regproxy_IP + ':' + \
                     regproxy_port + ': ' + peticion
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
        data = my_socket.recv(int(regproxy_port))
        # START_LOG
        evento_log = ' Received from ' + regproxy_IP + ':' + \
                      regproxy_port + ': ' + data.decode('utf-8')
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
        print('Recibido -- ', data.decode('utf-8'))
        data_recibido = data.decode('utf-8').split()
        if data_recibido[1] == '401':
            nonce = data_recibido[-1].split('=')[1]
            m = hashlib.sha1()
            m.update(bytes(nonce, 'utf-8'))
            m.update(bytes(password, 'utf-8'))
            response = m.hexdigest()
            peticion = peticion + 'Authorization: Digest response=' + response
            print('Enviando: ' + peticion)
            my_socket.send(bytes(peticion, 'utf-8') + b'\r\n\r\n')
            # START_LOG
            evento_log = ' Sent to ' + regproxy_IP + ':' + \
                         regproxy_port + ': ' + peticion
            hora = time.gmtime(time.time())
            makeLog(log_file, hora, evento_log)
            # END_LOG
            data = my_socket.recv(int(regproxy_port))
            # START_LOG
            evento_log = ' Received from ' + regproxy_IP + ':' + \
                          regproxy_port + ': ' + data.decode('utf-8')
            hora = time.gmtime(time.time())
            makeLog(log_file, hora, evento_log)
            # END_LOG
            print('Recibido -- ', data.decode('utf-8'))
    except socket.error:
        sys.exit('Error: No server listening at ' + regproxy_IP + ' port ' + \
                 regproxy_port)
        # START_LOG
        evento_log = 'Error: No server listening at ' + regproxy_IP + \
                     ' port ' + regproxy_port
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
elif metodo == 'INVITE':
    peticion = 'INVITE sip:' + opcion + ' SIP/2.0\r\n' + \
               'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' + \
               'o=' + username + ' ' + uas_ip + '\r\n' + 's=misesion\r\n' + \
               't=0\r\n' + 'm=audio ' + rtp_port + ' RTP\r\n'
    print('Enviando: ' + peticion)
    try:
        my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
        # START_LOG
        evento_log = ' Sent to ' + regproxy_IP + ':' + \
                     regproxy_port + ': ' + peticion
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
        data = my_socket.recv(int(regproxy_port))
        # START_LOG
        evento_log = ' Received from ' + regproxy_IP + ':' + \
                      regproxy_port + ': ' + data.decode('utf-8')
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
    except socket.error:
        sys.exit('Error: No server listening at ' + regproxy_IP + ' port ' + \
                 regproxy_port)
        # START_LOG
        evento_log = 'Error: No server listening at ' + regproxy_IP + \
                     ' port ' + regproxy_port
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
    print('Recibido -- ', data.decode('utf-8'))
    slices = data.decode('utf-8').split()
    if slices[1] == '100' and slices[4] == '180' and slices[7] == '200':
        metodo == 'ACK'
        peticion = 'ACK sip:' + opcion + ' SIP/2.0'
        ip_destino = slices[13] # destino del RTP
        port_destino = slices[17] # destino del RTP
        print('Enviando: ' + peticion)
        try:
            my_socket.send(bytes(peticion, 'utf-8') + b'\r\n\r\n')
            # START_LOG
            evento_log = ' Sent to ' + regproxy_IP + ':' + \
                         regproxy_port + ': ' + peticion
            hora = time.gmtime(time.time())
            makeLog(log_file, hora, evento_log)
            # END_LOG
            aEjecutar = './mp32rtp -i ' + ip_destino + ' -p ' + port_destino
            aEjecutar += ' < ' + audio_file
            print('Vamos a ejecutar', aEjecutar)
            os.system(aEjecutar)
            # START_LOG
            evento_log = ' Sending to ' + ip_destino + ':' + \
                          port_destino + ': ' + 'audio_file'
            hora = time.gmtime(time.time())
            makeLog(log_file, hora, evento_log)
            # END_LOG
            print('Finished transfer')
            vlc = 'cvlc rtp://@' + ip_destino + ':' + port_destino + \
                   ' 2> /dev/null'
            print(vlc)
            os.system(vlc)
            data = my_socket.recv(int(port_destino))
            # START_LOG
            evento_log = ' Finished audio transfer to ' + \
                         ip_destino + ':' + port_destino + \
                         ': ' + audio_file
            hora = time.gmtime(time.time())
            makeLog(log_file, hora, evento_log)
            # END_LOG
        except socket.error:
            sys.exit('Error: No server listening at ' + ip_destino + \
                     ' port ' + port_destino)
            # START_LOG
            evento_log = 'Error: No server listening at ' + regproxy_IP + \
                         ' port ' + regproxy_port
            hora = time.gmtime(time.time())
            makeLog(log_file, hora, evento_log)
            # END_LOG
        print('Recibido -- ', data.decode('utf-8'))
elif metodo == 'BYE':
    peticion = 'BYE sip:' + opcion + ' SIP/2.0'
    print('Enviando: ' + peticion)
    try:
        my_socket.send(bytes(peticion, 'utf-8') + b'\r\n\r\n')
        # START_LOG
        evento_log = ' Sent to ' + regproxy_IP + ':' + \
                     regproxy_port + ': ' + peticion
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
        data = my_socket.recv(int(regproxy_port))
        # START_LOG
        evento_log = ' Received from ' + regproxy_IP + ':' + \
                      regproxy_port + ': ' + data.decode('utf-8')
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
    except socket.error:
        sys.exit('Error: No server listening at ' + regproxy_IP + ' port ' + \
                 regproxy_port)
        # START_LOG
        evento_log = 'Error: No server listening at ' + regproxy_IP + \
                     ' port ' + regproxy_port
        hora = time.gmtime(time.time())
        makeLog(log_file, hora, evento_log)
        # END_LOG
    print('Recibido -- ', data.decode('utf-8'))

# START_LOG
evento_log = ' Finishing.'
hora = time.gmtime(time.time())
makeLog(log_file, hora, evento_log)
# END_LOG
