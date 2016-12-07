#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import random
import os
import hashlib
import time
import json

try:
    config = sys.argv[1]
except IndexError:
    sys.exit('Usage: python3 proxy_registrar.py config')

class XMLHandler(ContentHandler):

    def __init__(self):
        """Inicializador de varibles. config_dic es un diccionario en el que
            se guardaran los datos de cada etiqueta. data_list es una lista 
            donde se guardaran todos los diccionarios"""
        self.config_dic = {}
        self.data_list = []
       
    def startElement(self, name, attrs):
        if name == 'server':
            self.config_dic['name'] = attrs.get('name', '--')
            self.config_dic['ip'] = attrs.get('ip', '--')
            self.config_dic['port'] = attrs.get('port', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'database':
            self.config_dic['path'] = attrs.get('path', '--')
            self.config_dic['passwdpath'] = attrs.get('passwdpath', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
        elif name == 'log':
            self.config_dic['path'] =  attrs.get('path', '--')
            self.data_list.append(self.config_dic)
            self.config_dic = {}
            
    def get_data(self):
        return self.data_list

parser = make_parser()
XMLH = XMLHandler()
parser.setContentHandler(XMLH)
parser.parse(open(config))
data_list = XMLH.get_data()
# Variables del xml
server_name = data_list[0]['name']
serverIP = data_list[0]['ip']
serverPort = data_list[0]['port']
database_path = data_list[1]['path']
passwd_path = data_list[1]['passwdpath']
log_path = data_list[2]['path']


class RegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    data_client = {} # Diccionario de clientes registrados

    def register2json(self):
        """Metodo con el que cada vez que un usuario se registre o se de
        de baja, se imprimira en un fichero json con informacion sobre el
        usuario, su direccion y la hora de expiracion"""
        json.dump(self.data_client, open('registered.json', 'w'))

    def json2registered(self):
        """Metodo que comprobara si hay fichero json. Si hay, leera su
        contenido y lo usara como diccionario de usuarios. Si no hay, se
        ejecutara como si no hubiera fichero json"""
        try:
            with open('registered.json') as client_file:
                self.data_client = json.load(client_file)
                self.file_exists = True
        except:
            self.file_exists = False

    def delete(self):
        """Metodo que eliminara un cliente del diccionario si ha expirado"""
        tmpList = []
        self.t_actual = time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.gmtime(time.time()))
        for client in self.data_client:
            self.expire = int(self.data_client[client][-1])
            #print(self.data_client)
            now = time.time()
            #print("now", now, "expire", self.expire)
            if self.expire < now:
                tmpList.append(client)
        for cliente in tmpList:
            del self.data_client[cliente]
            print('ELIMINADO')
        self.register2json()

    def handle(self):
        while 1:
            line = self.rfile.read().decode('utf-8')
            print('El cliente nos manda: ' + line)
            if not line:
                break
            line_slices = line.split()
            metodo = line_slices[0]
            #nonce = random.randint(0000, 9999)
            if metodo == 'REGISTER':
                if 'Digest' not in line_slices:
                    self.wfile.write(b'SIP/2.0 401 Unauthorized\r\n')
                    self.wfile.write(b'WWW Authenticate: Digest nonce=45' )
                    #self.wfile.write(bytes(nonce))
                    self.wfile.write(b'\r\n\r\n')
                else:
                    self.nonce = '45'
                    self.user = line.split()[1].split(':')[1]
                    self.port = line.split()[1].split(':')[2]
                    hresponse = line.split()[-1].split('=')[1]
                    passwd_file = open(passwd_path, 'r')
                    passwd_file1 = passwd_file.readlines()
                    self.expires = line.split()[4]
                    for line in passwd_file1:
                        line_slices = line.split()
                        word = line_slices[1].split('\r\n')
                        if line_slices[0] == self.user:
                            password = word[0].split('=')[1]
                    m = hashlib.sha1()
                    m.update(bytes(self.nonce, 'utf-8'))
                    m.update(bytes(password, 'utf-8'))
                    response_comparation = m.hexdigest()
                    if response_comparation == hresponse:
                        self.json2registered()
                        self.now = time.time()
                        self.client_list = []
                        #self.client_list.append(user)
                        self.client_list.append(self.client_address[0]) # IP
                        self.client_list.append(self.port) # Puerto
                        self.client_list.append(self.now)
                        self.client_list.append(float(self.expires) +\
                              float(self.now))
                        self.data_client[self.user] = self.client_list
                        self.delete()
                        self.client_list = []
                    else:
                        self.wfile.write(b'SIP/2.0 404 User Not Found')
                    self.register2json()
                    print(self.data_client)
            elif metodo == 'INVITE':
                rtp_port = line.split()[-2]
                print(self.data_client)
                self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                self.wfile.write(b'SIP/2.0 180 Ring\r\n\r\n')
                self.wfile.write(b'SIP/2.0 200 OK\r\n')
                self.wfile.write(b'Content-Type: application/sdp\r\n\r\n')
                self.wfile.write(b'v=0\r\no=leonard@bigbang.com\r\n')
                self.wfile.write(b's=misesion\r\nt=0\r\n')
                self.wfile.write(b'm=audio ' + bytes(rtp_port, 'utf-8'))
                self.wfile.write(b' RTP')
                
            elif metodo == 'ACK':
                aEjecutar = 'mp32rtp -i ' + IP + ' -p 23032 < ' + audio_file
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
                print('Finished transfer')
            elif metodo == 'BYE':
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            elif metodo != 'REGISTER' or 'INVITE' or 'ACK' or 'BYE':
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad Request')


# Creamos servidor de eco y escuchamos
serv = socketserver.UDPServer((serverIP, int(serverPort)), RegisterHandler)
print('Server BigBangServer listening at port ' + serverPort + '...')
serv.serve_forever()            
