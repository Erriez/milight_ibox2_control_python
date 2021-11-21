#!/usr/bin/python

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
"""

import unittest
from milight_ibox2 import *


# Start with default iBox2 IP address and port
ibox_ip = "10.10.100.254"
ibox_port = 5987
ibox_timeout = 2
ibox_retries = 5
verbose = False
lamp_type = MilightIBox.RGBWW_TYPE
zone = 0


class TestMilightIBox(unittest.TestCase):
    def setUp(self):
        pass

    def test01_scan(self):
        global ibox_ip, ibox_port

        print("Testing scan...")
        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries = ibox_retries,
                           verbose=verbose)
        found_devices = ibox.scan()
        self.assertGreaterEqual(len(found_devices), 1)

        ibox_ip = found_devices[0]['ip']
        self.assertGreaterEqual(len(ibox_ip), 7)

        ibox_port = found_devices[0]['port']
        self.assertEqual(ibox_port, 5987)  # Always same USP port?

        self.assertEqual(len(found_devices[0]['mac']), 17)

    def test02_connect_disconnect(self):
        print("Testing connect/disconnect...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        self.assertEqual(ibox.is_connected(), False)
        ibox.connect()
        self.assertEqual(ibox.is_connected(), True)
        ibox.disconnect()
        self.assertEqual(ibox.is_connected(), False)

    def test03_timeout(self):
        print("Testing timeout...")

        # Assuming IP address is not assigned to an iBox2
        ibox = MilightIBox(ibox_ip="192.168.0.1", ibox_port=ibox_port, sock_timeout=ibox_timeout,
                           tx_retries=ibox_retries, verbose=verbose)
        self.assertEqual(ibox.is_connected(), False)
        ibox.connect()
        self.assertEqual(ibox.is_connected(), False)
        ibox.disconnect()

    def test04_light_on_off(self):
        print("Testing on/off...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.zone = zone
        ibox.lamp_type = lamp_type

        ibox.light(on=True)
        ibox.white()
        ibox.brightness(75)

        ibox.light_off()
        print("Is zone {} off? y/[n]".format(zone))
        self.assertEqual(input(), "y")

        ibox.light_on()
        print("Is zone {} on? y/[n]".format(zone))
        self.assertEqual(input(), "y")

        ibox.light_off()
        print("Is zone {} off? y/[n]".format(zone))
        self.assertEqual(input(), "y")

        ibox.night()
        print("Is zone {} night light? y/[n]".format(zone))
        self.assertEqual(input(), "y")

        ibox.disconnect()
        self.assertEqual(ibox.is_connected(), False)

    def test05_brightness(self):
        print("Testing brightness...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.zone = zone
        ibox.lamp_type = lamp_type

        ibox.light_on(zone)
        ibox.white(zone)

        ibox.brightness(1)
        print("Is zone {} brightness 1%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.brightness(25)
        print("Is zone {} brightness 25%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.brightness(100)
        print("Is zone {} brightness 100%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.brightness(75)
        print("Is zone {} brightness 75%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.brightness(50)
        print("Is zone {} brightness 50%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

    def test06_temperature(self):
        print("Testing color temperature...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.zone = 0
        ibox.lamp_type = lamp_type

        ibox.light_on()
        ibox.white()
        ibox.brightness(75)

        ibox.temperature(2700)
        print("Is zone {} temperature 2700K? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.temperature(6500)
        print("Is zone {} temperature 6500K? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.temperature(5500)
        print("Is zone {} temperature 5500K? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.temperature(4000)
        print("Is zone {} temperature 4000K? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

    def test07_color(self):
        print("Testing RGB...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.zone = 0
        ibox.lamp_type = lamp_type

        ibox.light_on()
        ibox.brightness(75)
        ibox.saturation(0)

        ibox.color_raw(ibox.RGB_RED)
        print("Is zone {} red? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.color_raw(ibox.RGB_GREEN)
        print("Is zone {} green? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.color_raw(ibox.RGB_BLUE)
        print("Is zone {} blue? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.saturation(100)
        print("Is zone {} saturation 100%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.saturation(50)
        print("Is zone {} saturation 50%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.saturation(0)
        print("Is zone {} saturation 0%? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.white()
        print("Is zone {} white? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

    def test08_mode(self):
        print("Testing mode...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.zone = zone
        ibox.lamp_type = lamp_type

        ibox.light_on()
        ibox.brightness(75)

        ibox.mode(1)
        print("Is zone {} mode 1? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

        ibox.mode(9)
        print("Is zone {} mode 9? y/[n]".format(ibox.zone))
        self.assertEqual(input(), "y")

    def test09_zones(self):
        print("Testing zones...")

        ibox = MilightIBox(ibox_ip=ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.zone = zone
        ibox.lamp_type = lamp_type

        ibox.light_off(0)
        print("Is zone 0 off? y/[n]")
        self.assertEqual(input(), "y")

        for _zone in range(1, 5):
            ibox.light_on()
            ibox.white()
            ibox.brightness(75)
            ibox.temperature(4000)
            print("Is zone {} on? y/[n]".format(ibox.zone))
            self.assertEqual(input(), "y")


if __name__ == '__main__':
    unittest.main()
