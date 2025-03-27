# load new csv dataset
# for each unique device_address create Nwkkey and Appkey, such as {dev_addr: (Nwk_key, App_key)}
import pandas as pd
import secrets
import json
import sys

def generate_keys():
        # generates random dev EUI and app_key for OTAA auth
        return(secrets.token_hex(8), secrets.token_hex(16), secrets.token_hex(16))

df = pd.read_csv(sys.argv[1])
print(df.head())
unique_dev_addresses = df.device_address.unique()
print(len(unique_dev_addresses))

credentials = {}
print(unique_dev_addresses)
print('number of unique dev addre', len(unique_dev_addresses))
for addr in unique_dev_addresses:
    credentials[addr] = generate_keys()

with open("device_credentials.json", "w") as outfile:
    json.dump(credentials, outfile)
