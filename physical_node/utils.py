from network import LoRa
import socket
import time
import binascii
import ujson
import struct 

# Initialise LoRa in LORAWAN mode.

#lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

#def setup_frequencies(a):


def join(dev_addr, nwk_swkey, app_swkey):
    dev_addr = struct.unpack(">l", binascii.unhexlify(dev_addr))[0]
    nwk_swkey = binascii.unhexlify(nwk_swkey)
    app_swkey = binascii.unhexlify(app_swkey)
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
    '''for i in range(3, 16):
        lora.remove_channel(i)

    # set the 3 default channels to the same frequency
    lora.add_channel(0, frequency=868100000, dr_min=0, dr_max=5)
    lora.add_channel(1, frequency=868100000, dr_min=0, dr_max=5)
    lora.add_channel(2, frequency=868100000, dr_min=0, dr_max=5)'''
    lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))


    print(str(dev_addr) + " has joined")
    return(lora.stats())

def send(dev_addr, nwk_swkey, app_swkey, pl_size, freq, SF, confirmed, fport):
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
    # unhexlifying credentials

    dev_addr_hex = dev_addr
    dev_addr = struct.unpack(">l", binascii.unhexlify(dev_addr))[0]
    nwk_swkey = binascii.unhexlify(nwk_swkey)
    app_swkey = binascii.unhexlify(app_swkey)

    #joining lorawan network
    lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

    print(str(dev_addr_hex) + " has joined")

    # create LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 12-int(SF))
    s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, confirmed)

    for i in range(0, 16):
        lora.remove_channel(i)

    # set the 3 default channels to the same frequency
    for i in range(0, 16):
        lora.add_channel(i, frequency=freq, dr_min=0, dr_max=5)


    s.setblocking(True)
    s.bind(fport)
    s.send(bytes(int(pl_size)))

    # send some data
    '''while True:
        s.send(bytes(int(pl_size)))
        print("sent bytes")
        time.sleep(1)'''
    s.setblocking(False)
    return lora.stats()[7]

   # s.setblocking(False)


#print("activated")

#send("00C77906", 'E9AD62163D82F60875C0A49A6E4784B1', 'CDD0A6B8A0D500DCAEE581EF681C5D2F', 3, 868100000, 12, False, 2)



#print(join('007C7A26', '3A0A75553402458E319D39924C31A335', 'B49CEBC289BDE164028A49D2B786521D'))

