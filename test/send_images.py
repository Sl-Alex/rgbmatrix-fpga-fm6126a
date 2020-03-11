#!/usr/bin/env python3

# Script outputs all images *.gif,*.png,*.jpg from its folder
# with some delay. Image size should match the display size.
#
# Requirements:
# 1. PyFTDI, installation details see this link:
#    https://eblot.github.io/pyftdi/installation.html
# 2. Pillow

import time
from pyftdi.spi import SpiController
from PIL import Image
from glob import glob

# Display size
DISP_W = 128
DISP_H = 32
# Bytes per pixel
BPP    = 2

# FTDI controller
FTDI_URL = 'ftdi://ftdi:4232:FTYX7ASG/1'

def initialize():
    global spi
    global gpio

    # Configure controller with one CS
    ctrl = SpiController(cs_count=1, turbo=True)

    #ctrl.configure('ftdi:///?')  # Use this if you're not sure which device to use
    # Windows users: make sure you've loaded libusb-win32 using Zadig
    ctrl.configure(FTDI_URL)

    # Get SPI slave
    # CS0, 10MHz, Mode 0 (CLK is low by default, latch on the rising edge)
    spi = ctrl.get_port(cs=0, freq=10E6, mode=0)

    # Get GPIO
    gpio = ctrl.get_gpio()
    gpio.set_direction(0x10, 0x10)


def send_image(fname):
    global gpio
    global spi

    # Create a buffer
    write_buf = bytearray(DISP_W*DISP_H*BPP)

    # Import an image
    im = Image.open(fname)
    im = im.convert('RGB')

    # Put it to the write buffer
    for y in range(0, DISP_H):
        for x in range(0, DISP_W):
            r, g, b = im.getpixel((x, y))
            # Convert to 4-bit color
            r = int(r*16/256);
            g = int(g*16/256);
            b = int(b*16/256);
            # Write two bytes
            write_buf[x*2 + y*DISP_W*2]     = r;
            write_buf[x*2 + y*DISP_W*2 + 1] = (g << 4) | b;

    # Toggle dat_ncfg pin. This will force internal address counter to zero.
    gpio.write(0x10)
    time.sleep(0.010)
    gpio.write(0x00)
    time.sleep(0.010)
    # Release dat_ncfg pin
    gpio.write(0x10)

    # Synchronous exchange with the remote SPI slave
    spi.exchange(write_buf, duplex=False)

###

initialize()
files=glob('*.gif')+glob('*.png')+glob('*.jpg')
for file in files:
    send_image(file)
    time.sleep(1)

print('Done')