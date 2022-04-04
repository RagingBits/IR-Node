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


def debug_print(data):
	global debug_Active
	if(True == debug_active):
		print(data)


def main():
	global socket_server_open

	socket_input_queue = queue.Queue()

	parser = argparse.ArgumentParser(description='IR Node command converter. It takes arguments and converts them to a byte array organizaton used by the IR node serial input.')

	parser.add_argument('-c', metavar='command', required=True, help='Comamnd to be sent to Node.(Mandatory field in decimal, binary (0bN) or hexa (0xn))')
	parser.add_argument('-a', metavar='address', required=True, help='Destination Node address.(Mandatory field in decimal, binary (0bN) or hexa (0xn))')
	parser.add_argument('-d', metavar='data', required=True, help='Command data to be set to Node.(Otional field in decimal, binary (0bN), hexa (0xn) or string.)')
	
	args = parser.parse_args()
	arg_counter = 0
	error = False
	command = ''
	address = ''

	data = ''

	try:#convert ints
		command = int(args.c,10)%64
		arg_counter += 1
	except:
		try:#convert hex
			command = int(args.c[2:],16)%64
			arg_counter += 1
		except:
			error = True

	if(not error):
		try:#convert ints
			address = int(args.a)%256
			arg_counter += 1
		except:
			try:#convert hex
				address = int(args.a[2:],16)%256
				arg_counter += 1
			except:
				error = True

	
	
	data_args = args.d.split(',')
	if(not error):
		for arg in data_args:
			if(data != ''):
				data += ' '
			
			try:#convert hex
				if(arg[0:2] == '0x'):
					val = int(arg[2:],16)
					debug_print("Hex: %d"%val)
					data += str(val%256) 
					val = int(val/256)
					while(val > 0):
						if(val != 0):
							data += ' '
						data += str(val%256) 
						val = int(val/256)
						
					arg_counter += 1
						
				else:
					raise ValueError(1)
			except:
				try:#convert bin	
					if(arg[0:2] == '0b'):
						val = int(arg[2:],2)
						debug_print("Bin: %d"%val)
						data += str(val%256) 
						val = int(val/256)
						while(val > 0):
							if(val != 0):
								data += ' '
							data += str(val%256) 
							val = int(val/256)

						arg_counter += 1
					else:
						raise ValueError(1)
				except:
					try:#convert ints
						val = int(arg,10)
						debug_print("Dec: %d"%val)
						data += str(val%256) 
						val = int(val/256)
						while(val > 0):
							if(val != 0):
								data += ' '
							data += str(val%256) 
							val = int(val/256)
						arg_counter += 1
					except:
						try:#convert ascii
							if(arg[0:1] == '\''):
								data += arg

							arg_counter += 1
						except:
							error = True
							break
	
	

	if(error):
		if(0 == arg_counter):
			debug_print("Invalid command.")
		elif(1 == arg_counter):
			debug_print("Invalid address.")
		else:
			debug_print("Invalid data arg: %i." %(arg_counter-2))
		os._exit(1)



	data = data.split(' ')
	debug_print(data)


	if(0 == command):# Set device with new address.
		debug_print("Change Node Address.")
		new_address = int(data[0])%256
		new_address_inv = (~new_address)%256

		command = command %64
		command += 1<<6

		packet = bytearray([address,command,new_address,new_address_inv])
		
	if(1 == command):# Set device uart speed.
		debug_print("Set UART Speed.")

		speed3 = int(data[2])
		speed2 = int(data[1])
		speed1 = int(data[0])

		command += 2<<6
		packet = bytearray([address,command,speed3,speed2,speed1,0x00])

	if(2 == command):# Send data to UART.
		debug_print("Send data to UART.")
		
		total_data = len(data)
		total_data_counter = 0
		len_counter = 0
		data_to_send = [0]*6
		while len_counter < 6 and total_data_counter < total_data:
			if data[total_data_counter][0:1] == '\'':
				bytes_in = bytes(data[total_data_counter][1:len(data[total_data_counter])-1] ,'UTF-8')
				bytes_in_counter = 0
				while len_counter < 6 and bytes_in_counter < len(bytes_in):
					data_to_send[len_counter] = bytes_in[bytes_in_counter]
					len_counter = len_counter+1
					bytes_in_counter = bytes_in_counter+1
			else:
				data_to_send[len_counter] = int(data[total_data_counter])%256
				len_counter = len_counter+1

			total_data_counter = total_data_counter+1

		if(len_counter>6):
			len_counter = 6

		len_counter = len_counter + len_counter%2

		val = len_counter/2
		val = (val)%0x04
		val = val * 64
		command = command % 64
		command += val
		command = int(command)

		if(len_counter>5):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256,data_to_send[2]%256,data_to_send[3]%256,data_to_send[4]%256,data_to_send[5]%256])
		elif(len_counter>4):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1],data_to_send[2]%256,data_to_send[3]%256,data_to_send[4]%256,0x00])
		elif(len_counter>3):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256,data_to_send[2]%256,data_to_send[3]%256])
		elif(len_counter>2):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256,data_to_send[2]%256,0x00])
		elif(len_counter>1):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256])
		elif(len_counter>0):
			packet = bytearray([address,command,data_to_send[0]%256,0x00])
		else:
			packet = bytearray([address,command])

	if(3 == command):# Get data from UART.
		debug_print("Get data from UART.")
		packet = bytearray([address,command])

	if(4 == command):# Confirm and read data from UART.
		debug_print("Confirm and get data from UART.")
		packet = bytearray([address,command])

	if(5 == command):# Read device PINS.
		debug_print("Read device IOs.")
		packet = bytearray([address,command])

	if(6 == command):# Set device PINS with new value.
		debug_print("Write device IOs.")
		command += 1<<6
		packet = bytearray([address,command,int(data[0])%256,int(data[1])%256])
		
	if(7 == command):# Setup I2C.
		debug_print("Setup device I2C.")
		command += 1<<6
		packet = bytearray([address,command,int(data[0])%256,0x00])

	if(8 == command):# Send through I2C.
		debug_print("Send data to device I2C.")

		total_data = len(data)
		total_data_counter = 0
		len_counter = 0
		data_to_send = [0]*6
		while len_counter < 6 and total_data_counter < total_data:
			if data[total_data_counter][0:1] == '\'':
				bytes_in = bytes(data[total_data_counter][1:len(data[total_data_counter])-1] ,'UTF-8')
				bytes_in_counter = 0
				while len_counter < 6 and bytes_in_counter < len(bytes_in):
					data_to_send[len_counter] = bytes_in[bytes_in_counter]
					len_counter = len_counter+1
					bytes_in_counter = bytes_in_counter+1
			else:
				data_to_send[len_counter] = int(data[total_data_counter])%256
				len_counter = len_counter+1

			total_data_counter = total_data_counter+1

		if(len_counter>6):
			len_counter = 6

		len_counter = len_counter + len_counter%2

		val = len_counter/2
		val = (val)%0x04
		val = val * 64
		command = command %64
		command += val
		command = int(command)

		if(len_counter>5):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256,data_to_send[2]%256,data_to_send[3]%256,data_to_send[4]%256,data_to_send[5]%256])
		elif(len_counter>4):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1],data_to_send[2]%256,data_to_send[3]%256,data_to_send[4]%256,0x00])
		elif(len_counter>3):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256,data_to_send[2]%256,data_to_send[3]%256])
		elif(len_counter>2):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256,data_to_send[2]%256,0x00])
		elif(len_counter>1):
			packet = bytearray([address,command,data_to_send[0]%256,data_to_send[1]%256])
		elif(len_counter>0):
			packet = bytearray([address,command,data_to_send[0]%256,0x00])
		else:
			packet = bytearray([address,command])


	if(9 == command):# Read from I2C.
		debug_print("Read data from device I2C.")

		total_data = len(data)
		total_data_counter = 0
		len_counter = 0
		data_to_send = [0]*6
		while len_counter < 6 and total_data_counter < total_data:
			if data[total_data_counter][0:1] == '\'':
				bytes_in = bytes(data[total_data_counter][1:len(data[total_data_counter])-1] ,'UTF-8')
				bytes_in_counter = 0
				while len_counter < 6 and bytes_in_counter < len(bytes_in):
					data_to_send[len_counter] = bytes_in[bytes_in_counter]
					len_counter = len_counter+1
					bytes_in_counter = bytes_in_counter+1
			else:
				data_to_send[len_counter] = int(data[total_data_counter])%256
				len_counter = len_counter+1

			total_data_counter = total_data_counter+1

		if(len_counter>6):
			len_counter = 6

		len_counter = len_counter + len_counter%2

		val = len_counter/2
		val = (val)%0x04
		val = val * 64
		command = command %64
		command += val
		command = int(command)


		if(len_counter>4):
			packet = bytearray([address,command,data_to_send[0]%256,0x00,0x00,0x00,0x00,0x00])
		elif(len_counter>2):
			packet = bytearray([address,command,data_to_send[0]%256,0x00,0x00,0x00])
		elif(len_counter>0):
			packet = bytearray([address,command,data_to_send[0]%256,0x00])
		else:
			packet = bytearray([address,command])


	if(10 == command):# Read device Info.
		debug_print("Get Node Info")

		packet = bytearray([address,command])

		
	data_out = ''.join('%d,' %i for i in packet)
	print(data_out[0:len(data_out)-1])

	
	debug_print("End")

	
	
	
	
if __name__ == "__main__":
	main()












