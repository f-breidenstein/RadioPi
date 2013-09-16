#!/usr/bin/env python3
from quick2wire.spi import *
from quick2wire.gpio import Pin
from quick2wire.gpio import In,Out,pi_header_1
import time
import sys
import unittest
import threading

a = ord('a')
SMALL_PAUSE = 0.05
BIG_PAUSE=0.5
ACK_HANDLING = 0x00
INITIAL_STATUS = 0x0A
RADIO_ENABLED_STATUS=  0x0A
RADIO_RECEIVING_ENABLED_STATUS= 0x3B
STATUS      = 0x07
RF_SETUP    = 0x06
EN_AA       = 0x01
READ_REG    = 0x00
WRITE_REG   = 0x20
FLUSH_RX    = 0xE2
RF_CH       = 0x05
RX_ADDR_P0  = 0x0A
RX_ADDR_P1  = 0x0B
RX_PW_P0    = 0x11
RX_PW_P1    = 0x12
TX_ADDR     = 0x10
WR_TX_PLOAD = 0xA0
RD_RX_PLOAD = 0x61

class NRF24L01P:
	def __init__(self):
		self.nrf24 = SPIDevice(0, 0)
		self.TX_ADDRESS = [a,a,a,a,a]
		self.RX_ADDRESS = [a,a,a,a,a]
		self.RADIO_CHANNEL = 0
		self.PAYLOAD_SIZE = 5
		self.RADIO_MODE = 0b00100110
		self.nrf24.speed_hz=500000
		self.radio_pin = pi_header_1.pin(12, direction=Out)
		self.radio_pin.open()
		self.radio_pin.value=0
		self.radio_pin.value=1
		self.radio_lock=threading.Lock()
		self.setupRadio()


	def doOperation(self,operation):
		"""Do one SPI operation"""
		toReturn = self.nrf24.transaction(operation)
		return toReturn

	def receiveData(self):
		"""Receive one or None messages from module"""
		with self.radio_lock:
			sta=self.doOperation(duplex([STATUS]))
			if(not((ord(sta[0]) & 0b00001110) == 0b00001110)):
				bytes = [RD_RX_PLOAD]
				for x in range(0,self.PAYLOAD_SIZE):
					bytes.append(0x00)
				ret = self.doOperation(duplex(bytes))
				return ret.pop()[1:]
			else:
				return None

	def sendData(self,toSend):
		with self.radio_lock:
			self.radio_pin.value=0
			#set TX address
			bytes = [WRITE_REG|TX_ADDR]
			bytes.extend(self.TX_ADDRESS)
			self.doOperation(writing(bytes))
			#set RX address in case we have autoack enabled
			bytes = [WRITE_REG|RX_ADDR_P1]
			bytes.extend(self.RX_ADDRESS)
			self.doOperation(writing(bytes))
			#write radio on into status register
			#write bytes into tx buffer
			bytes = [WR_TX_PLOAD]
			bytes.extend(toSend)
			self.doOperation(writing(bytes))
			self.doOperation(writing([WRITE_REG,RADIO_ENABLED_STATUS]))
			self.radio_pin.value=1

	def setReceiwing(self):
		""" Sets Module to receive Data"""
		with self.radio_lock:
			self.radio_pin.value=0
			bytes = [WRITE_REG|STATUS]
			bytes.append(RADIO_RECEIVING_ENABLED_STATUS)
			self.doOperation(writing(bytes))
			self.doOperation(writing([WRITE_REG,RADIO_RECEIVING_ENABLED_STATUS]))
			self.doOperation(writing([FLUSH_RX]))
			self.radio_pin.value=1

	def setupRadio(self):
			#Set RX address
			with self.radio_lock:
				self.radio_pin.value=0
				bytes = [WRITE_REG|RX_ADDR_P1]
				bytes.extend(self.RX_ADDRESS)
				self.doOperation(writing(bytes))
				bytes = [WRITE_REG|RF_CH]
				bytes.append(self.RADIO_CHANNEL)
				self.doOperation(writing(bytes))
				#Set Payload Sizes
				bytes = [WRITE_REG|RX_PW_P0]
				bytes.append(self.PAYLOAD_SIZE)
				self.doOperation(writing(bytes))
				bytes = [WRITE_REG|RX_PW_P1]
				bytes.append(self.PAYLOAD_SIZE)
				self.doOperation(writing(bytes))
				#Set Ack Handling
				bytes = [WRITE_REG|EN_AA]
				bytes.append(ACK_HANDLING)
				self.doOperation(writing(bytes))
				#Set Radio Mode
				bytes = [WRITE_REG|RF_SETUP]
				bytes.append(self.RADIO_MODE)
				self.doOperation(writing(bytes))
				#Reset status Register
				bytes = [WRITE_REG|STATUS]
				bytes.append(INITIAL_STATUS)
				self.doOperation(writing(bytes))
				#Flush RX Buffer
				self.doOperation(writing([FLUSH_RX]))
				self.radio_pin.value=1

if __name__ == "__main__":
	moduuli = NRF24L01P()
	test = sys.argv[1]
	bytesToSend = test.encode('utf-8')
	moduuli.sendData(bytesToSend)
	moduuli.sendData(bytesToSend)
	moduuli.sendData(bytesToSend)

