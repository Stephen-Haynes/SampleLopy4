from network import LoRa
import socket
import time
import binascii
import pycom
import ustruct
from machine import ADC

    # takes battery voltage readings
def adc_battery():
    # initialise adc hardware
    adc = ADC(0)
    #create an object to sample ADC on pin 16 with attenuation of 11db (config 3)
    adc_c = adc.channel(attn=3, pin='P16')
    # initialise the list
    adc_samples = []
    # take 100 samples and append them into the list
    for count in range(100):
        adc_samples.append(int(adc_c()))
    # sort the list
    adc_samples = sorted(adc_samples)
    # take the center list row value (median average)
    adc_median = adc_samples[int(len(adc_samples)/2)]
    # apply the function to scale to volts
    adc_median = adc_median * 2 / 4095 / 0.3275
    print(adc_samples)

    return adc_median



# disable LED heartbeat (so we can control the LED)
pycom.heartbeat(False)
# set LED to red
pycom.rgbled(0x7f0000)

# lora config
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AS923)
# access info
app_eui = binascii.unhexlify('70B3D57ED0012FC2')
app_key = binascii.unhexlify('6C3B6BD79C939C85AF19786EA4120057')

# attempt join - continues attempts background
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=100000)

# wait for a connection
print('Waiting for network connection...')
while not lora.has_joined():
    pass

# we're online, set LED to green and notify via print
pycom.rgbled(0x007f00)
print('Network joined!')

# setup the socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setblocking(False)
s.bind(1)


# sending some bytes
print('Sending 1,2,3')
s.send(bytes([1, 2, 3]))
time.sleep(3)



#text is automatically converted to a string, data heavy (dont do it this way)
print('Sending "Hello World"')
s.send("Hello World!")
time.sleep(3)


# check for a downlink payload, up to 64 bytes
rx_pkt = s.recv(64)

if len(rx_pkt) > 0:
    print("Downlink data on port 200:", rx_pkt)
    input("Downlink recieved, press any key to continue")

while True:
    lipo_voltage = adc_battery()

    print("Battery voltage:  ", lipo_voltage)
    # encode the packet, so that it's in BYTES (TTN friendly)
    # could be extended like this struct.pack('f',lipo_voltage) + struct.pack('c',"example text")
    packet = ustruct.pack('f',lipo_voltage)

    # send the prepared packet via LoRa
    s.send(packet)

    # example of unpacking a payload - unpack returns a sequence of
    #immutable objects (a list) and in this case the first object is the only object
    print ("Unpacked value is:", ustruct.unpack('f',packet)[0])

    time.sleep(3)
