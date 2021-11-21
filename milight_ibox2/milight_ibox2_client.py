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

    This Python script contains a MilightIBox class to communicate with the Milight WiFi iBox2
    Controller with version 6 protocol over UDP sockets.
"""

import socket
import time


def _print_bytearray(data, msg=""):
    """ Print bytearray in HEX
    :param data: bytearray
    :param msg:  String before the bytearray
    """
    line = msg
    for b in data:
        line += "%02X " % b
    print(line)


class MilightIBox:
    BRIDGE_TYPE = 0x00
    WALLWASHER_TYPE = 0x07
    RGBWW_TYPE = 0x08  # Default lamp type for RGB/WW/CCT

    RGB_LIGHT_PURPLE = 200
    RGB_PURPLE = 240
    RGB_RED = 10
    RGB_ORANGE = 25
    RGB_YELLOW = 40
    RGB_LIGHT_GREEN = 70
    RGB_GREEN = 95
    RGB_LIGHT_BLUE = 120
    RGB_BLUE = 180

    def __init__(self, ibox_ip='10.10.100.254', ibox_port=5987, sock_timeout=2, tx_retries=5, verbose=False):
        """ Milight iBox2 constructor
        :param ibox_ip: IP address of the iBox2
        :param ibox_port: UDP port of the iBox2 (default 5987)
        :param sock_timeout: Transfer timeout in seconds
        :param tx_retries: Number of transfer retries
        :param verbose: Print additional information
        """
        # Setup variables
        self._sock_server = None
        self._sock_timeout = sock_timeout
        self._tx_retries = tx_retries
        self._ibox_ip = ibox_ip
        self._ibox_port = ibox_port
        self._ibox_session_id1 = -1
        self._ibox_session_id2 = -1
        self._ibox_connected = False
        self._ibox_seq = 0
        self._zone = 0
        self._lamp_type = self.RGBWW_TYPE
        self._verbose = verbose

    def __del__(self):
        self._socket_close()

    # ----------------------------------------------------------------------------------------------
    # Network sockets
    # ----------------------------------------------------------------------------------------------
    def _socket_open(self):
        """ Open UDP socket """
        if not self._sock_server:
            if self._verbose:
                print("Socket open...")

            self._sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock_server.settimeout(self._sock_timeout)
            self._ibox_connected = False

    def _socket_send(self, data, broadcast=False):
        """ Send data to UDP socket
        :param data: bytearray
        :param broadcast: Broadcast IP 255.255.255.255 or ibox IP
        """
        if self._verbose:
            _print_bytearray(data, "  TX {}:{} {} Bytes: ".format(self._ibox_ip, self._ibox_port, len(data)))

        try:
            if broadcast:
                ibox_addr = ('255.255.255.255', self._ibox_port)
            else:
                ibox_addr = (self._ibox_ip, self._ibox_port)
            self._sock_server.sendto(data, ibox_addr)
            time.sleep(0.075)
        except socket.timeout:
            print("TX timeout")
        except Exception as ex:
            print("Error: ", ex)

    def _socket_recv(self, bufsize=1024):
        """ Receive synchronous data from UDP socket
        param bufsize: Receive buffer size (default: 1024 Bytes)
        return:
            bytearray: data, (string: addr, int: port)
            When a timeout or error occurs, it returns b(''), ('', -1)
        """
        data_bytes = bytearray()
        addr = ''
        port = -1

        try:
            # Wait for UDP response from iBox
            data_bytes, (addr, port) = self._sock_server.recvfrom(bufsize)

            # Check received data
            if not data_bytes:
                if self._verbose:
                    print("  RX {}:{} None".format(addr, port))
            else:
                # Convert received data to bytearray
                data_bytes = bytearray(data_bytes)

                if self._verbose:
                    _print_bytearray(data_bytes, "  RX {}:{} {} Bytes: ".format(addr, port, len(data_bytes)))
        except socket.timeout:
            if self._verbose:
                print("RX timeout")
        except Exception as ex:
            print("Error: RX ", ex)

        return data_bytes, (addr, port)

    def _socket_close(self):
        """ Close UDP socket
        :return: None
        """
        if self._verbose:
            print("Socket close...")

        if self._sock_server:
            self._sock_server.close()
            self._sock_server = None
        self._ibox_connected = False

    # ----------------------------------------------------------------------------------------------
    # Milight iBox2 functions
    # ----------------------------------------------------------------------------------------------
    def scan(self):
        """ Scan and return all iBox2 devices in network
        :return: List: [{'ip': '10.10.100.254', 'port': 5987, 'mac': 'F0:FE:6B:XX:XX:XX'}, ...]
        """
        found_ibox_devices = []
        data = bytearray([0x13, 0x00, 0x00, 0x00, 0x0a, 0x03, 0x9b, 0x7f, 0x11, 0xf0, 0xfe, 0x6b, 0x3b, 0xdd, 0xd4])

        self._socket_open()
        self._socket_send(data, broadcast=True)

        while 1:
            # Wait for UDP response from iBox
            rx_data, (ibox_addr, ibox_port) = self._socket_recv(100)

            # Check if data received, break on receive timeout
            if not rx_data:
                break

            # Basic check returned data
            if len(rx_data) == 69 and rx_data[0] == 0x18:
                ibox_mac = '{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}'.format(rx_data[6], rx_data[7], rx_data[8],
                                                                              rx_data[9], rx_data[10], rx_data[11])
                if ibox_port != (rx_data[49] << 8) | rx_data[50]:
                    if self._verbose:
                        print('Warning: Incorrect port received')
                        return
                else:
                    device = {'ip': ibox_addr, 'port': ibox_port, 'mac': ibox_mac}
                    if device not in found_ibox_devices:
                        found_ibox_devices.append(device)

        return found_ibox_devices

    def connect(self, ibox_ip=None, ibox_port=None):
        """ iBox connect by sending start session and retrieve session ID1 and ID2
        :param ibox_ip: iBox2 IP address
        :param ibox_port: iBox2 UDP port
        """
        # Fixed 22 Bytes
        cmd_start_session = bytearray([0x20, 0x00, 0x00, 0x00,  0x16, 0x02, 0x62, 0x3A,
                                       0xD5, 0xED, 0xA3, 0x01,  0xAE, 0x08, 0x2D, 0x46,
                                       0x61, 0x41, 0xA7, 0xF6,  0xDC, 0xAF, 0xD3, 0xE6,
                                       0x00, 0x00, 0x1E])

        # Fixed 7 Bytes start of session response
        resp_start_session = bytearray([0x28, 0x00, 0x00, 0x00, 0x11, 0x00, 0x02])

        if ibox_ip:
            self._ibox_ip = ibox_ip
        if ibox_port:
            self._ibox_port = ibox_port
        self._ibox_connected = False
        self._ibox_session_id1 = -1
        self._ibox_session_id2 = -1

        # Open UDP socket
        self._socket_open()

        for retry in range(0, self._tx_retries):
            if self._verbose:
                if retry == 0:
                    print("TX {}:{} start session...".format(self._ibox_ip, self._ibox_port))
                else:
                    print("TX {}:{} retry {}...".format(self._ibox_ip, self._ibox_port, retry))
            self._socket_send(cmd_start_session)
            rx_data = self._socket_recv()[0]
            if rx_data:
                if len(rx_data) != 22:
                    print("Error: Incorrect response length")
                    continue

                resp_header = rx_data[0:7]
                mac = rx_data[7:13]
                unknown1 = rx_data[13:19]
                session_id1 = rx_data[19:20]
                session_id2 = rx_data[20:21]
                unknown2 = rx_data[21:22]

                if self._verbose:
                    _print_bytearray(resp_header, "    Response:    ")
                    _print_bytearray(mac, "    MAC:         ")
                    _print_bytearray(unknown1, "    Unknown1:    ")
                    _print_bytearray(session_id1, "    Session ID1: ")
                    _print_bytearray(session_id2, "    Session ID2: ")
                    _print_bytearray(unknown2, "    Unknown2:    ")

                if resp_header != resp_start_session:
                    print("Error: Incorrect response header")

                self._ibox_connected = True
                self._ibox_session_id1 = session_id1[0]
                self._ibox_session_id2 = session_id2[0]
                self._ibox_seq = 0
                return

    def disconnect(self):
        """ iBox disconnect """
        if self._ibox_connected:
            self._socket_close()
            self._ibox_connected = False

    def is_connected(self):
        """ Check if already connected to the iBox
        :return: True: Connected or False: Not connected
        """
        return self._ibox_connected

    def send_command(self, light_command):
        """ Send light command
        :param light_command: bytearray 11 Bytes
        """
        if len(light_command) != 11:
            print("Error: Incorrect command argument")
            return

        if not self._ibox_connected:
            print("Error: Not connected")
            return

        # Calculate checksum on light command + zone
        checksum = 0
        for b in light_command:
            checksum += b
        checksum &= 0xff

        for retry in range(0, self._tx_retries):
            if self._verbose:
                if retry == 0:
                    print("TX send command...")
                else:
                    print("TX retry %d..." % retry)

            cmd = bytearray([0x80, 0x00, 0x00, 0x00, 0x11,
                             self._ibox_session_id1, self._ibox_session_id2, 0x00,
                             self._ibox_seq, 0x00]) + light_command + bytearray([checksum])

            send_seq = self._ibox_seq
            self._ibox_seq += 0x01
            self._ibox_seq &= 0xFF

            self._socket_send(cmd)
            rx_data = self._socket_recv()[0]
            if rx_data:
                if len(rx_data) != 8:
                    print("Error: Incorrect response length")
                elif rx_data[0:6] != bytearray([0x88, 0x00, 0x00, 0x00, 0x03, 0x00]):
                    print("Error: Incorrect response header")
                elif rx_data[6] != send_seq:
                    print("Error: Incorrect sequence response")
                else:
                    # Response received
                    break

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, zone):
        if (zone < 0) or (zone > 4):
            raise "Error: Incorrect zone"
        else:
            self._zone = zone

    @property
    def lamp_type(self):
        return self._lamp_type

    @lamp_type.setter
    def lamp_type(self, lamp_type):
        self._lamp_type = lamp_type & 0xFF

    def light(self, on, zone=None, lamp_type=None):
        """ Turn light on
        :param on: True: Turn light on, False: Turn light off
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send light on zone %d..." % zone)

        if on:
            light_cmd = 0x01
        else:
            light_cmd = 0x02

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x04, light_cmd, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def light_on(self, zone=None, lamp_type=None):
        """ Turn light on
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        self.light(on=True, zone=zone, lamp_type=lamp_type)

    def light_off(self, zone=None, lamp_type=None):
        """ Turn light off
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        self.light(on=False, zone=zone, lamp_type=lamp_type)

    def night(self, zone=None, lamp_type=None):
        """ Turn night light on
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send night light on zone %d..." % zone)

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x04, 0x05, 0x00, 0x00, 0x00, zone, 0x00]))

    def white(self, zone=None, lamp_type=None):
        """ Turn white on, RGB off
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send white light on (RGB off) zone %d..." % zone)

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x05, 0x64, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def color_raw(self, rgb, zone=None, lamp_type=None):
        """ Set color raw 8-bit value
        :param rgb: 0x00..0xff
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if (rgb < 0) or (rgb > 0xff):
            raise ValueError("RGB must be a value of 0..255")

        if self._verbose:
            print("Send RGB color 0x%02X zone %d..." % (rgb, zone))

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x01, rgb, rgb, rgb, rgb, zone & 0x07, 0x00]))

    def saturation(self, saturation, zone=None, lamp_type=None):
        """ Set saturation when RGB is on
        :param saturation: 0..100
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if (zone < 0) or (zone > 100):
            raise ValueError("Saturation must be a value of 0..100")

        if self._verbose:
            print("Send saturation %d%% zone %d..." % (saturation, zone))

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x02, saturation, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def brightness(self, brightness, zone=None, lamp_type=None):
        """ Set brightness
        :param brightness: 0..100 (Note: 0 is not off)
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if (brightness < 0) or (brightness > 100):
            raise ValueError("Brightness must be a value of 0..100")

        if self._verbose:
            print("Send brightness %d%% zone %d..." % (brightness, zone))

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x03, brightness, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def temperature(self, temperature, zone=None, lamp_type=None):
        """ Set temperature
        :param temperature: 2700..6500
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if (temperature < 2700) or (temperature > 6500):
            raise ValueError("Temperature must be a value of 2700..6500")

        if self._verbose:
            print("Send color temperature %dK zone %d..." % (temperature, zone))

        # Calculate color temperature byte
        ct = int((temperature - 2700) / ((6500-2700)/100)) & 0xFF

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x05, ct, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def mode(self, mode, zone=None, lamp_type=None):
        """ Decrease speed when light is in mode 1..9
        :param mode: 1..9 (Blink/flash/glow etc)
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if (mode < 1) or (mode > 9):
            raise ValueError("Mode must be a value of 1..9")

        if self._verbose:
            print("Send mode %d zone %d..." % (mode, zone))

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x06, mode, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def mode_speed_decrease(self, zone=None, lamp_type=None):
        """ Decrease speed when light is in mode 1..9
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send mode speed-- zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x04, 0x04, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def mode_speed_increase(self, zone=None, lamp_type=None):
        """ Increase speed when light is in mode 1..9
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send mode speed++ zone %d..." % zone)

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type & 0xFF,
                                     0x04, 0x03, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def link(self, zone=None, lamp_type=None):
        """ Link light
            Send this command within 3 seconds after connecting the light to the main power
        :param zone: 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send link zone %d..." % zone)

        self.send_command(bytearray([0x3D, 0x00, 0x00, lamp_type & 0xFF,
                                     0x00, 0x00, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))

    def unlink(self, zone=None, lamp_type=None):
        """ Unlink light
            Send this command within 3 seconds after connecting the light to the main power
        :param zone: 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        """
        if not zone:
            zone = self._zone
        if not lamp_type:
            lamp_type = self._lamp_type

        if self._verbose:
            print("Send link zone %d..." % zone)

        self.send_command(bytearray([0x3E, 0x00, 0x00, lamp_type & 0xFF,
                                     0x00, 0x00, 0x00, 0x00, 0x00, zone & 0x07, 0x00]))
