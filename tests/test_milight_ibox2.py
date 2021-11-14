#!/usr/bin/python

import unittest
from milight_ibox2.milight_ibox2_control import MilightIBox


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

    def test_connect_disconnect(self):
        print("Testing connect/disconnect...")

        ibox = MilightIBox(ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        self.assertEqual(ibox.is_connected(), False)
        ibox.connect()
        self.assertEqual(ibox.is_connected(), True)
        ibox.disconnect()
        self.assertEqual(ibox.is_connected(), False)

    def test_timeout(self):
        print("Testing timeout...")

        ibox = MilightIBox(ibox_ip="192.168.0.1", ibox_port=ibox_port, sock_timeout=ibox_timeout,
                           tx_retries=ibox_retries, verbose=verbose)
        self.assertEqual(ibox.is_connected(), False)
        ibox.connect()
        self.assertEqual(ibox.is_connected(), False)
        ibox.disconnect()

    def test_light_on_off(self):
        print("Testing on/off...")
        ibox = MilightIBox(ibox_ip,
                           ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries, verbose=verbose)
        ibox.connect()
        ibox.send_light_on(zone)
        ibox.send_white_light_on(zone)
        ibox.send_brightness(75, zone)

        ibox.send_light_off(0)
        print("Are all lights off? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_light_on(zone)
        print("Are all lights on? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_light_off(zone)
        print("Are all lights off? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_night_light_on(zone)
        print("Are all lights in night light? y/[n]")
        self.assertEqual(input(), "y")

        ibox.disconnect()

    def test_light_brightness(self):
        print("Testing brightness...")

        ibox = MilightIBox(ibox_ip,
                           ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries, verbose=verbose)
        ibox.connect()
        ibox.send_light_on(zone)
        ibox.send_white_light_on(zone)

        ibox.send_brightness(1, zone)
        print("Is brightness of all lights 1%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_brightness(25, zone)
        print("Is brightness of all lights 25%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_brightness(100, zone)
        print("Is brightness of all lights 100%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_brightness(75, zone)
        print("Is brightness of all lights 75%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_brightness(50, zone)
        print("Is brightness of all lights 50%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.disconnect()

    def test_color_temperature(self):
        print("Testing color temperature...")

        ibox = MilightIBox(ibox_ip,
                           ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries, verbose=verbose)
        ibox.connect()
        ibox.send_light_on(zone)
        ibox.send_white_light_on(zone)
        ibox.send_brightness(75, zone)

        ibox.send_color_temperature(2700, zone)
        print("Is color temperature of all lights 2700K? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_color_temperature(6500, zone)
        print("Is color temperature of all lights 6500K? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_color_temperature(5500, zone)
        print("Is color temperature of all lights 5500K? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_color_temperature(4000, zone)
        print("Is color temperature of all lights 4000K? y/[n]")
        self.assertEqual(input(), "y")

        ibox.disconnect()

    def test_rgb(self):
        print("Testing RGB...")

        ibox = MilightIBox(ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.send_light_on(zone)
        ibox.send_brightness(75, zone)
        ibox.send_saturation(0, zone)

        ibox.send_rgb_color(0x10, zone)
        print("Is RGB color of all lights red? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_rgb_color(0x60, zone)
        print("Is RGB color of all lights green? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_rgb_color(0xb0, zone)
        print("Is RGB color of all lights blue? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_saturation(100, zone)
        print("Is saturation of all lights 100%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_saturation(50, zone)
        print("Is saturation of all lights 50%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_saturation(0, zone)
        print("Is saturation of all lights 0%? y/[n]")
        self.assertEqual(input(), "y")

        ibox.disconnect()

    def test_mode(self):
        print("Testing mode...")

        ibox = MilightIBox(ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()
        ibox.send_light_on(zone)
        ibox.send_brightness(75, zone)

        ibox.send_mode(1, zone)
        print("Is mode 1? y/[n]")
        self.assertEqual(input(), "y")

        ibox.send_mode(9, zone)
        print("Is mode 9? y/[n]")
        self.assertEqual(input(), "y")

    def test_zones(self):
        print("Testing zones...")

        ibox = MilightIBox(ibox_ip, ibox_port=ibox_port, sock_timeout=ibox_timeout, tx_retries=ibox_retries,
                           verbose=verbose)
        ibox.connect()

        ibox.send_light_off(0)
        print("Are all lights off? y/[n]")
        self.assertEqual(input(), "y")

        for _zone in range(1, 5):
            ibox.send_light_on(_zone)
            ibox.send_white_light_on(_zone)
            ibox.send_brightness(75, _zone)
            ibox.send_color_temperature(4000, _zone)
            print("Is light %d on? y/[n]" % _zone)
            self.assertEqual(input(), "y")

        ibox.disconnect()


if __name__ == '__main__':
    unittest.main()
