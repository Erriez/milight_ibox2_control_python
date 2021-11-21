#!/usr/bin/env python3

"""
    MIT License

    Copyright (c) 2017-2020 Erriez

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    Milight iBox2 example with Python3
"""

import time

from milight_ibox2.milight_ibox2_control import MilightIBox

# Create iBox2 object
ibox2 = MilightIBox(ibox_ip='10.10.100.154', ibox_port=5987, sock_timeout=2, tx_retries=5, verbose=False)

# Scan for devices
print('Scan MiLight iBox2 devices...')
found_devices = ibox2.scan()
if not found_devices:
    print('No devices found')
    exit(0)

print('Found {} iBox2 devices:'.format(len(found_devices)))
for device in found_devices:
    print('  {}:{} ({})'.format(device['ip'], device['port'], device['mac']))

    # Connect
    print('Connecting to {}:{}'.format(device['ip'], device['port']))
    ibox2.connect(ibox_ip=device['ip'], ibox_port=device['port'])

    # Set lamp type:
    #   LampType.BRIDGE_TYPE = 0x00
    #   LampType.WALLWASHER_TYPE = 0x07
    #   LampType.RGBWW_TYPE = 0x08  # Default lamp type for RGB/WW/CCT
    # Or specify a different lamp type number (0..255).
    ibox2._lamp_type = ibox2.RGBWW_TYPE

    # zone 0=all, 1..4
    for zone in range(0, 4):
        # Set zone
        ibox2.zone = zone

        print('Zone {} off...'.format(ibox2.zone))
        ibox2.light_off()
        time.sleep(1)

        print('Zone {} on...'.format(ibox2.zone))
        ibox2.light_on()

        print('Zone {} off...'.format(ibox2.zone))
        ibox2.light(on=False)
        time.sleep(1)

        print('Zone {} on...'.format(ibox2.zone))
        ibox2.light(on=True)

        tmp_zone = 4
        print('Zone {} off...'.format(tmp_zone))
        ibox2.light(on=False, zone=tmp_zone)
        time.sleep(1)

        print('Zone {} on...'.format(tmp_zone))
        ibox2.light(on=True, zone=tmp_zone)
        time.sleep(1)

        brightness = 75
        print('Zone {} set brightness {}...'.format(ibox2.zone, brightness))
        ibox2.brightness(brightness)
        time.sleep(1)

        saturation = 0
        print('Zone {} set saturation {}...'.format(ibox2.zone, saturation))
        ibox2.saturation(saturation)
        for color in [ibox2.RGB_LIGHT_PURPLE,
                      ibox2.RGB_PURPLE,
                      ibox2.RGB_RED,
                      ibox2.RGB_ORANGE,
                      ibox2.RGB_YELLOW,
                      ibox2.RGB_LIGHT_GREEN,
                      ibox2.RGB_GREEN,
                      ibox2.RGB_LIGHT_BLUE,
                      ibox2.RGB_BLUE]:
            print('Zone {} set color {}...'.format(ibox2.zone, color))
            ibox2.color_raw(color)
            time.sleep(1)

        print('Zone {} set white mode...'.format(ibox2.zone))
        ibox2.white(color)
        time.sleep(1)

        for saturation in [127, 255]:
            print('Zone {} set saturation {}...'.format(ibox2.zone, saturation))
            ibox2.saturation(saturation)
            time.sleep(1)

        for mode in [1, 9]:
            print('Zone {} set mode {}...'.format(ibox2.zone, mode))
            ibox2.mode(mode)
            time.sleep(1)

        for temperature in [6500, 2700]:
            print('Zone {} set temperature {}...'.format(ibox2.zone, temperature))
            ibox2.temperature(temperature)
            time.sleep(1)

        brightness = 5
        print('Zone {} set brightness {}'.format(ibox2.zone, brightness))
        ibox2.brightness(brightness)
        time.sleep(1)

        print('Zone {} night light on...'.format(ibox2.zone))
        ibox2.night()
        time.sleep(1)

    # Disconnect
    ibox2.disconnect()

    # Wait
    time.sleep(3)

print('Done')
