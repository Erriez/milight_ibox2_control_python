#!/usr/bin/env python3
import time

from milight_ibox2.milight_ibox2_control import MilightIBox

# Create iBox2 object
ibox2 = MilightIBox(ibox_ip='10.10.100.154', ibox_port=5987, sock_timeout=2, tx_retries=5, verbose=False)

# Specify optional lamp types:
#   LampType.BRIDGE_TYPE = 0x00
#   LampType.WALLWASHER_TYPE = 0x07
#   LampType.RGBWW_TYPE = 0x08  # Default lamp type for RGB/WW/CCT
# Or specify a different lamp type number.
lamp_type = MilightIBox.RGBWW_TYPE

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

    # zone 0=all, 1..4
    for zone in range(0, 4):
        print('Turn light {} off'.format(zone))
        ibox2.send_light_off(zone, lamp_type)
        time.sleep(1)
        print('Turn light zone {} on and set brightness / temperature'.format(zone))
        ibox2.send_light_on(zone, lamp_type)
        ibox2.send_brightness(75, zone)
        time.sleep(1)
        ibox2.send_color_temperature(6500, zone)
        time.sleep(1)
        ibox2.send_color_temperature(2700, zone)
        time.sleep(1)
        ibox2.send_brightness(5, zone)
        time.sleep(1)
        ibox2.send_night_light_on(zone)
        time.sleep(1)

    # Disconnect
    ibox2.disconnect()

    # Wait
    time.sleep(3)

print('Done')
