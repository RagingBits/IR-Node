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

debug_active = True
serial_in_thr = Thread
serial_out_thr = Thread
socket_in_thr = Thread
socket_out_thr = Thread
threads_run = False
thread_ser_in_active = False
thread_ser_out_active = False
serial_port = serial

total_sems = 2
current_sem =1
sem_val = 0
	

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
			time.sleep(0.001)
			if(port.isOpen() == True):
				temp_data = port.read(1) 
				if(temp_data):
					input_q.put(temp_data)
					#debug_print(temp_data)
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
			time.sleep(0.001)
			if(port.isOpen() == True):
				if(not output_q.empty()):
					data_raw = output_q.get()
					#debug_print(data_raw)
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


sem_vals=[1,2,4]
def sem_update(output_queue):
	global total_sems
	global current_sem
	global sem_val
	debug_print("Sem update")
	
	if(current_sem > total_sems):
		sem_val += 1
		current_sem = 1
		if(sem_val > 2):
			sem_val = 0
	
	
	debug_print([current_sem,70,3,sem_val+1])
	output_queue.put([current_sem,70,sem_vals[sem_val],3])
	current_sem += 1
	
	

def main():
	global serial_port
	global socket_port
	global socket_open
	global serial_input_queue
	global serial_output_queue

	serial_input_queue = queue.Queue()
	serial_output_queue = queue.Queue()

	parser = argparse.ArgumentParser(description='Node IO test consisting in circulating IO1 and IO2 values through 0b01, 0b10 and 0b11. ')

	parser.add_argument('-c', metavar='com_port', required=True, help='Serial COM port.(Mandatory argument.)')	
	args = parser.parse_args()

	port_name = args.c

	#serial_port = serial_start(port_name,input_queue,output_queue)
	serial_port = serial_start(port_name,serial_input_queue,serial_output_queue)

	#debug_print(data)
	data_in = ''
	max_counter = 10000
	data_counter = 0
	data_pointer = 0
	timeout_counter = 0
	timeout_val = 50
	byte_in = 0	
	sem_update(serial_output_queue)
	while(1):
		while(not serial_input_queue.empty()):
			byte_in = serial_input_queue.get(1)
			data_in += str(byte_in)
			data_counter += 1
			if(data_counter == 2):
				max_counter = (int.from_bytes(byte_in,'big')/64)*2

		if(data_counter > max_counter+1):
			timeout_counter = 0
			debug_print('Received:')
			debug_print(data_in[0:len(data_in)-1])
			timeout_counter = 0
			data_in = ''
			max_counter = 1000
			data_counter = 0
			sem_update(serial_output_queue)
				
		time.sleep(0.001)
		timeout_counter += 1
		if(timeout_counter >= timeout_val):
			debug_print('Timeout')
			timeout_counter = 0
			data_in = ''
			max_counter = 1000
			data_counter = 0
			sem_update(serial_output_queue)
			



	debug_print("End")

	
	
	
	
if __name__ == "__main__":
	main()