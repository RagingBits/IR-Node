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

serial_in_thr = Thread
serial_out_thr = Thread

socket_in_thr = Thread
socket_out_thr = Thread

threads_run = False

thread_ser_in_active = False
thread_ser_out_active = False
serial_port = serial

thread_socket_in_active = False
thread_socket_out_active = False

socket_input_queue = queue
socket_output_queue = queue

socket_port = socket
socket_connection = ''
socket_address = ''
socket_open = False

debug_active = True


def debug_print(data):
	global debug_Active

	if(True == debug_active):
		print(data)

def serial_in(port, input_q):
	global threads_run
	global thread_ser_in_active
	thread_ser_in_active = True
	debug_print("Serial In daemon started")
	try:
		while(thread_ser_in_active == True and threads_run == True):
			if(port.isOpen() == True):
				temp_data = port.read(100) 
				if(temp_data):
					input_q.put(temp_data)
				#print(data)
			else:
				thread_ser_in_active = False
	except:
		pass
		
	debug_print("Serial In daemon stopped")
	thread_ser_in_active = False
	threads_run = False
	
def serial_out(port, output_q):
	global thread_ser_out_active
	global threads_run
	thread_ser_out_active = True
	debug_print("Serial Out daemon started")
	try:
		while(thread_ser_out_active == True and threads_run == True):
			if(port.isOpen() == True):
				if(not output_q.empty()):
					data_raw = output_q.get()
					
					#try:
					#	data = bytes(data_raw,'UTF-8')
					#except:
					data = data_raw
					
					port.write(data)
				else:
					pass
			else:
				thread_ser_out_active = False
	except:
		thread_ser_out_active = False
		
	debug_print("Serial Out daemon stopped")
	thread_ser_out_active = False
	threads_run = False

def serial_start(port_name, input_queue, output_queue):
	global threads_run
	global thread_ser_in_active
	global thread_ser_out_active
	serial_port = serial.Serial()
	debug_print("Start serial connection.")
	while(serial_port.isOpen() == False):	
		time.sleep(1)
		
		if(thread_ser_in_active == False and thread_ser_out_active == False):
			debug_print("Attempt to open serial port...")
			try:
				serial_port = serial.Serial(
				port=port_name,
				baudrate=9600,
				parity=serial.PARITY_NONE,
				stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS,
				timeout=1)
				debug_print("Serial port open.")
				time.sleep(1)
			except:
				debug_print("Failed.")

		else:
			debug_print("Serial daemons still active.")

	threads_run = True
	debug_print("Start serial daemons.")
	serial_in_thr = Thread(target=serial_in, args=(serial_port, input_queue))
	serial_in_thr.daemon = True # thread dies with the program
	serial_in_thr.start()
	
	serial_out_thr = Thread(target=serial_out, args=(serial_port, output_queue))
	serial_out_thr.daemon = True # thread dies with the program
	serial_out_thr.start()
		
	return serial_port

def serial_stop():	
	global serial_in_thr
	global serial_out_thr
	global serial_port
	
	debug_print("Close serial connection.")
	serial_port.close()
	debug_print("Close serial daemons.")
	threads_run = False
	debug_print("Waiting serial daemons to stop...")
	while(thread_ser_in_active == True or thread_ser_out_active == True):
		debug_print(".")
		time.sleep(1)
		
	debug_print("Serial daemons stopped.")


def socket_in(socket,input_q):
	global threads_run
	global thread_socket_in_active
	global socket_open
	global socket_connection

	thread_socket_in_active = True
	debug_print("Socket In daemon started")
	try:
		while(thread_socket_in_active == True and threads_run == True):
			try:
				if(socket_open is True):
					temp_data = socket_connection.recv(1) 
					if(not temp_data):
						socket_open = False
						socket_connection.close()
					else:
						input_q.put(temp_data)
					#print(data)
				else:			
					socket_wait_connection()
			except:
				socket_open = False
				socket_wait_connection()
	except:
		debug_print("Socket In daemon ERROR")
		
	debug_print("Socket In daemon stopped")
	thread_socket_in_active = False
	
def socket_out(socket,output_q):
	global thread_socket_out_active
	global threads_run
	global socket_open
	global socket_connection

	thread_socket_out_active = True
	debug_print("Socket Out daemon started")
	try:
		while(thread_socket_out_active == True and threads_run == True):
			if(socket_open is True):
				if(not output_q.empty()):
					data_raw = output_q.get()
					socket_connection.send(data_raw)
				else:
					pass
			else:
				pass
	except:
		thread_socket_out_active = False
		debug_print("Socket Out daemon ERROR")
		
	debug_print("Socket Out daemon stopped")
	thread_socket_out_active = False

def socket_start(socket_type, input_queue, output_queue, sock_number):

	global threads_run
	global thread_socket_in_active
	global thread_socket_out_active
	global socket_in_thr
	global socket_out_thr
	global socket_port


	plt = platform.system()

	if plt == "Windows":
		# Windows com port
		socket_port = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	else:
		# Unix com port
		socket_port = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


	socket_port.bind(('localhost', sock_number))

	socket_port.listen(0)
	
	
	debug_print("Start socket IO daemons.")

	socket_in_thr = Thread(target=socket_in, args=(socket_port,input_queue))
	socket_in_thr.daemon = True # thread dies with the program
	socket_in_thr.start()
	
	socket_out_thr = Thread(target=socket_out, args=(socket_port,output_queue))
	socket_out_thr.daemon = True # thread dies with the program
	socket_out_thr.start()
		
	return socket_port.getsockname()[1]


def socket_wait_connection():

	global socket_port
	global socket_connection
	global socket_address
	global socket_open
	global socket_input_queue
	global socket_output_queue

	if(not socket_open):
		#with socket_input_queue.mutex:
		#	socket_input_queue.queue.clear()

		#with socket_output_queue.mutex:
		#	socket_output_queue.queue.clear()

		debug_print("Waiting socket connection...")
		
		socket_connection, socket_address = socket_port.accept()

	debug_print("Client connected.")
	socket_open = True

def socket_stop():	
	global socket_in_thr
	global socket_out_thr
	global socket_port
	
	debug_print("Close socket connection.")
	socket_port.close()

	debug_print("Close socket daemons.")
	threads_run = False
	debug_print("Waiting serial daemons to stop...")
	while(thread_ser_in_active == True or thread_ser_out_active == True):
		debug_print(".")
		time.sleep(1)
		
	debug_print("Socket daemons stopped.")

def main ():

	global serial_port
	global socket_port
	global socket_open
	global socket_input_queue
	global socket_output_queue

	socket_input_queue = queue.Queue()
	socket_output_queue = queue.Queue()

	parser = argparse.ArgumentParser(description='Serial to Local Socket bridge. Opens a socket that is piped directly to the indicated COM port.')

	parser.add_argument('-c', metavar='com_port', required=True, help='Serial COM port. (Mandatory argument.)')
	parser.add_argument('-s', metavar='socket_port', required=False, help='Socket port. (Optional argument. If not given a random free one will be attributed.)')
	
	args = parser.parse_args()

	port_name = args.c

	#serial_port = serial_start(port_name,input_queue,output_queue)
	serial_port = serial_start(port_name,socket_output_queue,socket_input_queue)
	
	if(not args.s):
		socket_number = 0
	else:
		socket_number = int(args.s)
		
	#open socket here

	if 'COM' in port_name:
		#print(socket_start("WIN", socket_input_queue, socket_output_queue))
		print(socket_start("WIN", socket_input_queue, socket_output_queue, int(socket_number)))
	else:
		#print(socket_start("UNIX", socket_input_queue, socket_output_queue))
		print(socket_start("UNIX", socket_input_queue, socket_output_queue,int(socket_number)))


	run = True

	while(run):
		
		time.sleep(0.01)

		if sys.stdin.readline() == 'x\n':
			run = False

	serial_stop();
	debug_print("End")



if __name__ == "__main__":
	main()