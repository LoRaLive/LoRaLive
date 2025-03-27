import utils
import json
import time
import uos
import machine
from network import WLAN
import _thread

# Load WiFi credentials from config file
with open("wifi_config.json") as wifi_file:
    wifi_conf = json.load(wifi_file)
    SSID = wifi_conf["ssid"]
    PASSWORD = wifi_conf["password"]

def ntp_syn(rtc):
    while True:
        rtc.ntp_sync("pool.ntp.org")
        while not rtc.synced():
            machine.idle()
        print("RTC synced with NTP time")
        time.timezone(1 * 60**2)  # GMT+2
        print(time.localtime())
        time.sleep(64)

def wlan_connect():
    wlan = WLAN(mode=WLAN.STA)
    while not wlan.isconnected():
        print("connecting to WiFi")
        wlan.connect(ssid=SSID, auth=(WLAN.WPA2, PASSWORD))
        time.sleep(1)
    print("connected to WiFi")

def WLAN_connect(wlan, attempts_number, ip_address=None):
    print("Connecting...")
    while attempts_number > 0:
        if ip_address:
            wlan.ifconfig(config=(ip_address, '255.255.255.0', '192.168.4.1', '8.8.8.8'))
        try:
            wlan.connect(ssid=SSID, auth=(WLAN.WPA2, PASSWORD), timeout=5000)
            while not wlan.isconnected():
                machine.idle()
            print("Connected to WiFi\n")
            return 0
        except:
            wlan.disconnect()
            attempts_number -= 1
            print("not connected, attempts left", attempts_number)
            time.sleep(1)

def ntp_connect(attempts_number):
    print("Connecting to ntp...")
    while attempts_number > 0:
        rtc = machine.RTC()
        print("syncing with ntp")
        try:
            rtc.ntp_sync("pool.ntp.org")
            while not rtc.synced():
                rtc.ntp_sync("pool.ntp.org")
            return 0
        except:
            wlan.disconnect()
            attempts_number -= 1
            print("not connected, attempts left", attempts_number)
            time.sleep(1)

id = machine.unique_id()

wlan = WLAN(mode=WLAN.STA)
WLAN_connect(wlan, 2, '')

rtc = machine.RTC()
print("sync with ntp")
rtc.ntp_sync("time.windows.com")
while not rtc.synced():
    machine.idle()
print("RTC synced with NTP time")
time.timezone(1 * 60**2)  # GMT+2
print(time.localtime())
_thread.start_new_thread(ntp_syn, (rtc,))

# Load device credentials
with open("device_credentials.json") as json_file:
    devices = json.load(json_file)
    print("loaded device credentials")

csv_file = 'device.csv'
print("reading file", csv_file)
with open(csv_file) as datafile:
    newline = datafile.readline()
    print(newline)
    newline = datafile.readline()
    print("waiting to start...")
    while rtc.now()[5] != 10:
        pass

    start_time = float(newline.split(",")[0])
    if start_time > 0.001:
        print("sleeping for", str(start_time), "seconds")
        time.sleep(start_time)

    while newline:
        try:
            print("packet to send:")
            print(newline)
            values = newline.split(",")
            dev_addr = values[1]
            nwk_swkey = devices[dev_addr][2]
            app_swkey = devices[dev_addr][1]
            pl_size = int(float(values[2])) - 13
            freq = int(values[3])
            SF = int(float(values[4]))
            confirmed = str(values[5]) == '100'
            fport = int(values[6])

            toa = utils.send(dev_addr, nwk_swkey, app_swkey, pl_size, freq, SF, confirmed, fport)
            print("payload_size:", pl_size, "SF:", SF, "ToA:", toa)

            extra_delay = float(values[9]) + float(values[10])

            if values[7][:-2]:
                wait_time = float(values[7][:-2])
                time_diff = wait_time - extra_delay
                if time_diff > 0.1:
                    print("sleeping until the next packet", time_diff, "\n")
                    time.sleep(time_diff)
                else:
                    print("sending the next packet right now", time_diff, "\n")
            else:
                break

            newline = datafile.readline()
        except:
            print("exception raised")
            newline = datafile.readline()

datafile.close()
print('Datafile read.')
