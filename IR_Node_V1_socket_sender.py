#########################################################################################################
# Developed by Raging Bits. (2022)																		#
# This code is provided free and to be used at users own responsability.								#
#########################################################################################################
import subprocess
import os
import sys
import time
import queue
import socket,os
from subprocess import PIPE, Popen
from threading  import Thread
import io
import serial
import argparse
import os.path
from pathlib import Path
import sys
import platform 

debug_active = False
socket_server_open = False


def debug_print(data):
	global debug_Active
	if(True == debug_active):
		print(data)



def main():
	global socket_server_open

	socket_input_queue = queue.Queue()

	parser = argparse.ArgumentParser(description='IR_Node_Sender')

	parser.add_argument('-s', metavar='socket', required=True, help='Socket given by the Serial2LocalSocket app.')
	parser.add_argument('-d', metavar='data', required=True, help='Command data to be set to Node.')
	
	args = parser.parse_args()

	data = list(map(int,args.d.split(',')))
	sockt = int(args.s)

	plt = platform.system()

	if plt == "Windows":
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	else:
		s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	s.connect(('localhost',sockt))

	debug_print(data)
	s.send(bytearray(data))

	s.settimeout(1)
	data_in = ''
	max_counter = 1000
	data_counter = 0
	while(1):
		try:
			byte_in = int.from_bytes(s.recv(1),byteorder='little') 
			data_in +=  ''.join('%d,' %byte_in)

			data_counter += 1
			if(data_counter == 2):
					max_counter = (byte_in/64)*2;
					debug_print("MC: %d"%max_counter)

			if(data_counter > max_counter+1):
				break

		except socket.timeout:
			break

	debug_print('Received:')
	print(data_in[0:len(data_in)-1])
	socket_server_open = False

	s.close()
	
	
	time.sleep(0.1)
	debug_print("End")

	
	
	
	
if __name__ == "__main__":
	main()