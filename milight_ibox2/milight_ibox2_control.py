""" This Python script contains a MilightIBox class to communicate with the Milight WiFi iBox2
    Controller with version 6 protocol over UDP sockets.
"""

import socket
import time


class MilightIBox:
    BRIDGE_TYPE = 0x00
    WALLWASHER_TYPE = 0x07
    RGBWW_TYPE = 0x08  # Default lamp type for RGB/WW/CCT

    def __init__(self, ibox_ip='10.10.100.254', ibox_port=5987, sock_timeout=2, tx_retries=5, verbose=False):
        """ Milight iBox2 constructor
        :param ibox_ip: IP address of the iBox2
        :param ibox_port: UDP port of the iBox2 (default 5987)
        :param sock_timeout: Transfer timeout in seconds
        :param tx_retries: Number of transfer retries
        :param verbose: Print additional information
        """
        # Setup variables
        self.sock_server = None
        self.sock_timeout = sock_timeout
        self.tx_retries = tx_retries
        self.ibox_ip = ibox_ip
        self.ibox_port = ibox_port
        self.ibox_session_id1 = -1
        self.ibox_session_id2 = -1
        self.ibox_connected = False
        self.ibox_seq = 0
        self.verbose = verbose

    # ----------------------------------------------------------------------------------------------
    # Network sockets
    # ----------------------------------------------------------------------------------------------
    def socket_open(self):
        """ Open UDP socket
        :return: None
        """
        if not self.sock_server:
            if self.verbose:
                print("Socket open...")

            self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock_server.settimeout(self.sock_timeout)
            self.ibox_connected = False

    def socket_send(self, data, broadcast=False):
        """ Send data to UDP socket
        :param data: bytearray
        :param broadcast: Broadcast IP 255.255.255.255 or ibox IP
        :return: None
        """
        if self.verbose:
            self.print_bytearray(data, "  TX %d Bytes: " % len(data))

        try:
            if broadcast:
                ibox_addr = ('255.255.255.255', self.ibox_port)
            else:
                ibox_addr = (self.ibox_ip, self.ibox_port)
            self.sock_server.sendto(data, ibox_addr)
            time.sleep(0.075)
        except socket.timeout:
            print("Error: TX timeout")
        except Exception as ex:
            print("Error: ", ex)

    def socket_recv(self, bufsize=1024):
        """ Receive synchronous data from UDP socket """
        try:
            # Wait for UDP response from iBox
            (data, addr) = self.sock_server.recvfrom(bufsize)
            # Convert received data to bytearray
            data = bytearray(data)
        except socket.timeout:
            print("Error: RX timeout")
            return
        except Exception as ex:
            print("Error: ", ex)
            return

        if self.verbose:
            self.print_bytearray(data, "  RX %d Bytes: " % len(data))

        return data, addr

    def socket_close(self):
        """ Close UDP socket
        :return: None
        """
        if self.verbose:
            print("Socket close...")
        self.sock_server.close()
        self.sock_server = None
        self.ibox_connected = False

    # ----------------------------------------------------------------------------------------------
    # Debug functions
    # ----------------------------------------------------------------------------------------------
    @staticmethod
    def print_bytearray(data, msg=""):
        """ Print bytearray in HEX
        :param data: bytearray
        :param msg:  String before the bytearray
        :return: None
        """
        line = msg
        for b in data:
            line += "%02X " % b
        print(line)

    # ----------------------------------------------------------------------------------------------
    # Milight iBox2 functions
    # ----------------------------------------------------------------------------------------------
    def scan(self):
        """ Scan and return all iBox2 devices in network
        :return: List: [{'ip': '10.10.100.254', 'port': 5987, 'mac': 'F0:FE:6B:XX:XX:XX'}, ...]
        """
        found_ibox_devices = []
        data = bytearray([0x13, 0x00, 0x00, 0x00, 0x0a, 0x03, 0x9b, 0x7f, 0x11, 0xf0, 0xfe, 0x6b, 0x3b, 0xdd, 0xd4])

        self.socket_open()
        self.socket_send(data, broadcast=True)

        while 1:
            try:
                # Wait for UDP response from iBox
                (data, (ibox_addr, ibox_port)) = self.sock_server.recvfrom(100)

                if self.verbose:
                    self.print_bytearray(data, "  RX %d Bytes: " % len(data))

                # Convert received data to bytearray
                rx_data = bytearray(data)
            except socket.timeout:
                # Timeout, no more devices replied
                break
            except Exception as ex:
                print("Error: ", ex)
                return

            # Basic check returned data
            if rx_data and len(rx_data) == 69 and rx_data[0] == 0x18:
                ibox_mac = '{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}'.format(rx_data[6], rx_data[7], rx_data[8],
                                                                              rx_data[9], rx_data[10], rx_data[11])
                if ibox_port != (rx_data[49] << 8) | rx_data[50]:
                    if self.verbose:
                        print('Warning: Incorrect port received')
                        return
                else:
                    device = {'ip': ibox_addr, 'port': ibox_port, 'mac': ibox_mac}
                    if device not in found_ibox_devices:
                        found_ibox_devices.append(device)

        return found_ibox_devices

    def connect(self, ibox_ip=None, ibox_port=None):
        """ iBox connect by sending start session and retrieve session ID1 and ID2
        :return: None
        """
        # Fixed 22 Bytes
        cmd_start_session = bytearray([0x20, 0x00, 0x00, 0x00,  0x16, 0x02, 0x62, 0x3A,
                                       0xD5, 0xED, 0xA3, 0x01,  0xAE, 0x08, 0x2D, 0x46,
                                       0x61, 0x41, 0xA7, 0xF6,  0xDC, 0xAF, 0xD3, 0xE6,
                                       0x00, 0x00, 0x1E])

        # Fixed 7 Bytes start of session response
        resp_start_session = bytearray([0x28, 0x00, 0x00, 0x00, 0x11, 0x00, 0x02])

        if ibox_ip:
            self.ibox_ip = ibox_ip
        if ibox_port:
            self.ibox_port = ibox_port
        self.ibox_connected = False
        self.ibox_session_id1 = -1
        self.ibox_session_id2 = -1

        self.socket_open()

        for retry in range(0, self.tx_retries):
            if self.verbose:
                if retry == 0:
                    print("TX start session...")
                else:
                    print("TX retry %d..." % retry)
            self.socket_send(cmd_start_session)
            rx_data, (rx_addr, rx_port) = self.socket_recv()
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

                if self.verbose:
                    self.print_bytearray(resp_header, "    Response:    ")
                    self.print_bytearray(mac, "    MAC:         ")
                    self.print_bytearray(unknown1, "    Unknown1:    ")
                    self.print_bytearray(session_id1, "    Session ID1: ")
                    self.print_bytearray(session_id2, "    Session ID2: ")
                    self.print_bytearray(unknown2, "    Unknown2:    ")

                if resp_header != resp_start_session:
                    print("Error: Incorrect response header")

                self.ibox_connected = True
                self.ibox_session_id1 = session_id1[0]
                self.ibox_session_id2 = session_id2[0]
                self.ibox_seq = 0
                return

    def disconnect(self):
        """ iBox disconnect
        :return: None
        """
        if self.ibox_connected:
            self.socket_close()
            self.ibox_connected = False

    def is_connected(self):
        """ Check if already connected to the iBox
        :return: True or False
        """
        return self.ibox_connected

    def send_command(self, light_command):
        """ Send light command
        :param light_command: bytearray 11 Bytes
        :return: None
        """
        if len(light_command) != 11:
            print("Error: Incorrect command argument")
            return

        if not self.ibox_connected:
            print("Error: Not connected")
            return

        # Calculate checksum on light command + zone
        checksum = 0
        for b in light_command:
            checksum += b
        checksum &= 0xff

        for retry in range(0, self.tx_retries):
            if self.verbose:
                if retry == 0:
                    print("TX start session...")
                else:
                    print("TX retry %d..." % retry)

            cmd = bytearray([0x80, 0x00, 0x00, 0x00, 0x11,
                             self.ibox_session_id1, self.ibox_session_id2, 0x00,
                             self.ibox_seq, 0x00]) + light_command + bytearray([checksum])

            send_seq = self.ibox_seq
            self.ibox_seq += 0x01
            self.ibox_seq &= 0xFF

            self.socket_send(cmd)
            rx_data, (rx_addr, rx_port) = self.socket_recv()
            if rx_data:
                if len(rx_data) != 8:
                    print("Error: Incorrect response length")
                    continue

                if rx_data[0:6] != bytearray([0x88, 0x00, 0x00, 0x00, 0x03, 0x00]):
                    print("Error: Incorrect response header")
                    continue

                if rx_data[6] != send_seq:
                    print("Error: Incorrect sequence response")
                    continue

                break

    def send_light_on(self, zone, lamp_type=RGBWW_TYPE):
        """ Turn light on
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send light on zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x04, 0x01, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_light_off(self, zone, lamp_type=RGBWW_TYPE):
        """ Turn light off
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send light off zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x04, 0x02, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_night_light_on(self, zone, lamp_type=RGBWW_TYPE):
        """ Turn night light on
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send night light on zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x04, 0x05, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_white_light_on(self, zone, lamp_type=RGBWW_TYPE):
        """ Turn white on, RGB off
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send white light on (RGB off) zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x05, 0x64, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_rgb_color(self, rgb, zone, lamp_type=RGBWW_TYPE):
        """ Set RGB color
        :param rgb: 0x00..0xff
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (rgb < 0) or (rgb > 0xff):
            print("Error: Incorrect RGB")
            return
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send RGB color 0x%02X zone %d..." % (rgb, zone))
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x01, rgb, rgb, rgb, rgb, zone, 0x00]))

    def send_saturation(self, saturation, zone, lamp_type=RGBWW_TYPE):
        """ Set saturation when RGB is on
        :param saturation: 0..100
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 100):
            print("Error: Incorrect saturation")
            return
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send saturation %d%% zone %d..." % (saturation, zone))
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x02, saturation, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_brightness(self, brightness, zone, lamp_type=RGBWW_TYPE):
        """ Set color temperature
        :param brightness: 0..100 (Note: 0 is not off)
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (brightness < 0) or (brightness > 100):
            print("Error: Incorrect brightness")
            return
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send brightness %d%% zone %d..." % (brightness, zone))
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x03, brightness, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_color_temperature(self, color_temperature, zone, lamp_type=RGBWW_TYPE):
        """ Set color temperature
        :param color_temperature: 2700..6500
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (color_temperature < 2700) or (color_temperature > 6500):
            print("Error: Incorrect brightness")
            return

        if self.verbose:
            print("Send color temperature %dK zone %d..." % (color_temperature, zone))

        # Calculate color temperature byte
        ct = int((color_temperature - 2700) / ((6500-2700)/100)) & 0xFF

        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x05, ct, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_mode(self, mode, zone, lamp_type=RGBWW_TYPE):
        """ Decrease speed when light is in mode 1..9
        :param mode: 1..9 (Blink/flash/glow etc)
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (mode < 1) or (mode > 9):
            print("Error: Incorrect mode")
            return
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send mode %d zone %d..." % (mode, zone))
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x06, mode, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_mode_speed_decrease(self, zone, lamp_type=RGBWW_TYPE):
        """ Decrease speed when light is in mode 1..9
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send mode speed-- zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x04, 0x04, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_mode_speed_increase(self, zone, lamp_type=RGBWW_TYPE):
        """ Increase speed when light is in mode 1..9
        :param zone: 0=all, 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send mode speed++ zone %d..." % zone)
        self.send_command(bytearray([0x31, 0x00, 0x00, lamp_type,
                                     0x04, 0x03, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_link(self, zone, lamp_type=RGBWW_TYPE):
        """ Link light
            Send this command within 3 seconds after connecting the light to the main power
        :param zone: 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send link zone %d..." % zone)
        self.send_command(bytearray([0x3D, 0x00, 0x00, lamp_type,
                                     0x00, 0x00, 0x00, 0x00, 0x00, zone, 0x00]))

    def send_unlink(self, zone, lamp_type=RGBWW_TYPE):
        """ Unlink light
            Send this command within 3 seconds after connecting the light to the main power
        :param zone: 1..4
        :param lamp_type: 0: Bridge, 7: Wallwasher, 8: RGB/WW/CCT (default)
        :return: None
        """
        if (zone < 0) or (zone > 4):
            print("Error: Incorrect zone")
            return

        if self.verbose:
            print("Send link zone %d..." % zone)
        self.send_command(bytearray([0x3E, 0x00, 0x00, lamp_type,
                                     0x00, 0x00, 0x00, 0x00, 0x00, zone, 0x00]))
