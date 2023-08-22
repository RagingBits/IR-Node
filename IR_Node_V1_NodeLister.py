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
import IR_Node_V1_socket_sender

debug_active = True

def debug_print(data):
	global debug_Active
	if(True == debug_active):
		print(data)

def main():

	parser = argparse.ArgumentParser(description='Node IO test consisting in circulating IO1 and IO2 values through 0b01, 0b10 and 0b11. ')

	parser.add_argument('-s', metavar='serial port socket', required=True, help='Serial COM port socket.(Mandatory argument.)')	
	args = parser.parse_args()

	socket_name = args.s

	#debug_print(data)
	max_counter = 256
	data_counter = 0
	
	while(data_counter < max_counter):

		data = str(int(data_counter)) + ",10"
		debug_print("Dev: {}".format(data_counter))
		debug_print(IR_Node_V1_socket_sender.main_app(socket_name,data))
		data_counter+=1

	debug_print("End")

	
	
	
	
if __name__ == "__main__":
	main()