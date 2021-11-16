# milight_ibox2_control_python

Milight iBox2 Controller interface with Python3 by using UDP socket.
  
Official Milight products: https://www.milight.com/
  
iBox2 limitations:
* Max 4-zones.
* No password protection.
* Plain UDP Ethernet communication.

Note: `Milight iBox2` product has been renamed to `Milight WiFi Box`. It is unclear if these
products are fully compatible with each other. Please let me know by creating an issue or 
pull-request.


## Milight iBox v6 protocol

```
1. Send start session packet to iBox IP at UDP port 5987
2. Get session ID1 and ID2 from response packet
3. Send light command to iBox

----------------------------------------------------------------------------------------------------
Start session to retrieve session ID1 and ID2 (TX 22 Bytes, RX 22 Bytes):
      +---------------+
      |     0..21     |
 TX:  +---------------+
      | START_SESSION |
      +---------------+

      +--------------+----------+---------+--------+--------+--------+
      |     0..6     |  7..12   | 13..18  | 19..19 | 20..20 | 21..21 |
 RX:  +--------------+----------+---------+--------+--------+--------+
      | RESP_SESSION | IBOX_MAC | UNKNOWN |  ID1   |  ID2   |   00   |
      +--------------+----------+---------+--------+--------+--------+

 TX:
   START_SESSION: 22 Bytes:
                  20 00 00 00 16 02 62 3A D5 ED A3 01 AE 08 2D 46 61 41 A7 F6 DC AF D3 E6 00 00 1E
 RX:
    RESP_SESSION:  7 Bytes:  28 00 00 00 11 00 02
    IBOX_MAC:      6 Bytes:  MAC address of the iBox
    UNKNOWN:       6 Bytes:  Undocumented, unused
    ID1:           1 Byte:   Session ID1
    ID2:           1 Byte:   Session ID2
    00:            1 Byte:   Always 0x00

----------------------------------------------------------------------------------------------------
Send command  (TX 22 Bytes, RX 8 Bytes):
      +---------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
      |  0..4   |  5..5  |  6..6  |  7..7  |  8..8  |  9..9  | 10..18 | 19..19 | 20..20 | 21..21 |
 TX:  +---------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
      |START_CMD|  ID1   |  ID2   |   00   |  SEQ   |   00   |  CMD   |  ZONE  |   00   |  CSUM  |
      +---------+--------+--------+--------+--------+--------+--------+--------+--------+--------+

      +---------+--------+--------+
      |  0..5   |  6..6  |  7..7  |
 RX:  +---------+--------+--------+
      |RESP_CMD |  SEQ   |   00   |
      +---------+--------+--------+

 TX:
     START_CMD:     5 Bytes:  80 00 00 00 11
     ID1:           1 Byte:   Session ID1
     ID2:           1 Byte:   Session ID2
     00:            1 Byte:   Always 0x00
     SEQ:           1 Byte:   Sequence number
     00:            1 Byte:   Always 0x00
     CMD:           9 Bytes:  Command
                              1 Byte:  31  Start
                              2 Bytes: 00  Password (Not used, always 0x00)
                              1 Byte:  08 for RGBW/WW/CW (default) or 00 for bridge lamp
                              5 Bytes: LIGHT_COMMAND
     ZONE:          1 Byte:   Zone number 1..4, 0=All
     00:            1 Byte:   Always 0x00
     CSUM:          1 Byte:   Checksum is the sum of the CMD and ZONE bytes.

 RX:
     RESP_CMD:      6 Bytes:  88 00 00 00 03 00
     SEQ:           1 Byte:   Sequence
     00:            1 Byte:   Always 0x00

 LIGHT_COMMANDs:
     04 01 00 00 00   Light ON
     04 02 00 00 00   Light OFF
     04 05 00 00 00   Night light ON
     05 64 00 00 00   White light ON (Color RGB OFF)
     01 CO CO CO CO   RGB_COLOR   (CO values 0x00..0xFF)
     02 SS 00 00 00   SATURATION (SS values 0x00..0x64)
     03 BN 00 00 00   BRIGHTNESS (BN values 0x00..0x64)
     05 CT 00 00 00   COLOR_TEMPERATURE (CT values 0x00..0x64)
     06 MO 00 00 00   Mode number (MO values 0x01..0x09)
     04 04 00 00 00   Mode speed decrease
     04 03 00 00 00   Mode speed increase
     00 00 00 00 00   Link (Sync Bulb within 3 seconds after lightbulb main power on)
     00 00 00 00 00   UnLink (Clear Bulb within 3 seconds after lightbulb main power on)

 RGB_COLOR:
     10 = Red
     15 = Orange
     30 = Yellow
     60 = Green
     B0 = Blue
     F0 = Magenta

 SATURATION and BRIGHTNESS:
     00 = 0%
     19 = 25%
     32 = 50%
     4B = 75%
     64 = 100%

 COLOR_TEMPERATURE:
     00 = 2700K  ~2700K (Warm White)
     08 = 3004K  ~3000K
     15 = 3498K  ~3500K
     22 = 3992K  ~4000K
     30 = 4524K  ~4500K
     3D = 5018K  ~5000K
     4A = 5512K  ~5500K
     57 = 6006K  ~6000K
     64 = 6500K  ~6500K (Cool White)
```


## Installation

The project can be installed als package. It is recommended to create a `virtualenv` first:

```bash
# Create virtual environment. Make sure virtualenv is installed.
$ virtualenv venv
$ source venv/bin/activate

# Install this project as package
$ python3 setup.py install
```


## Usage

```python
from milight_ibox2.milight_ibox2_control import MilightIBox

# Configure iBox IP address, for example:
ibox_ip = "10.10.100.254"

# Create object
ibox = MilightIBox(ibox_ip, ibox_port=5987, sock_timeout=2, tx_retries=5, verbose=False)

# Specify optional lamp types:
#   LampType.BRIDGE_TYPE = 0x00
#   LampType.WALLWASHER_TYPE = 0x07
#   LampType.RGBWW_TYPE = 0x08  # Default lamp type for RGB/WW/CCT
# Or specify a different lamp type number.
lamp_type = MilightIBox.RGBWW_TYPE

# Set zone: 0=all, 1..4
zone = 0

# Connect
ibox.connect()

# Send light on (zone 0=all, 1..4)
ibox.send_light_on(zone, lamp_type)

# Send white on
ibox.send_white_light_on(zone, lamp_type)

# Send brightness 75%
ibox.send_brightness(75, zone, lamp_type)

# Send color temperature 2700K
ibox.send_color_temperature(2700, zone, lamp_type)

# Send light off
ibox.send_light_off(zone, lamp_type)

# Disconnect
ibox.disconnect()
```


## Run tests

Each manual test asks confirmation from the user if the light responded correctly. 

```bash
# Start virtualenv first
$ source venv/bin/activate

# Run tests
$ python3 tests/test_milight_ibox2.py
```


## iBox2 WiFi configuration

### Factory reset

To enter AP mode factory reset:
* Connect USB power to the iBox2.
* Hold down `RST` for 5 seconds, fast blink `Link` and `SYS` LED's for 2 seconds, then SYS LED blinks.

Notes:
* Press `RST` once short enters `Smart Link Mode` and is not used.
* An iBox2 factory reset keeps synced lights, it resets WiFi configuration only, such as AP mode, password etc.

### Connect iBox2 to WiFi AP (manual configuration)

* Connect from smartphone/tablet/laptop/RaspberryPi WiFi to iBox WiFi `Milight3.0-XXXXXX`:

![AP+STA mode](assets/ConnectiBox2WiFi.jpg)

* Open a web browser and visit: http://admin:admin@10.10.100.254. (Username and password is `admin`)
* Click Work Mode: `AP+STA mode` | `Save` | `Restart`:

![AP+STA mode](assets/iBoxSettings01.jpg)

* Click `STA` | `Scan` | Select you WiFi AP | `OK` | Enter WiFi password | `Save` | `Restart`:

![AP+STA mode](assets/iBoxSettings02.jpg)

* Click Account and enter a new iBox2 password:

![AP+STA mode](assets/iBoxSettings03.jpg)

* Keep default `Other Settings`:

![AP+STA mode](assets/iBoxSettings04.jpg)

* Click Work Mode: `STA mode` | `Save` | `Restart`. (This disables iBox2 external WiFi access)
* Now the iBox2 can be accessed from internal network: `http://admin:admin@<IP or hostname>`

### Mi-Light 3.0 Android App

* Connect to WiFi with internet.
* Open Android App store and search/install [Mi-Light 3.0](https://play.google.com/store/apps/details?id=com.irainxun.wifilight).
* Click `Searching for device` and select `Mi-Light` device.
* Now the App is ready to use.

![Android MiLight 3.0 Screenshot](assets/MiLight3.0Screenshot.jpg)

**Important notes:** 

The Mi-Light 3.0 Android app asks for a wide range of permissions which looks like Chinese spyware:
  * Location (WTF, not required!)
  * Telephone status and ID (WTF, not required!)
  * Pictures/media/files/directories (WTF, not required!)
  * Storage (WTF, not required!)
  * Camera (WTF, not required!)
  * Information about device ID and conversations (WTF, not required!)
  * WiFi access (Ok, that's required)

There is no good reason to allow access to all privacy information above.

**Security warning:**

The internal iBox2 interface chip contains a standard WiFi to serial adapter `HF-LPB100` and stores the WiFi password in 
**plain text**. 
When the default password / `AP+STA mode` is set, an attacker can login and click 
`STA Settings` | check: `Show passwords`.
