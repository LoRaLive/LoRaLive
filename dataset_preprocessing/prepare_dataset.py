import pandas as pd
import datetime
import base64
import sys
from utils import calc_ToA
import pickle
import numpy as np

def convert_to_unix_ts(date):
# convert the date to unix timestamp format (e.g. 2022-02-12T00:02:22.333Z converts to 102934.231 or so)
    date = date[:-1]
    if len(date.split(".")[1]) > 3:
        date = date.split(".")[0] + '.' + str(round(float("0."+date.split(".")[1]), 3)).split('.')[1]
    date_format = datetime.datetime.strptime(date,"%Y-%m-%dT%H:%M:%S.%f")
    unix_time = datetime.datetime.timestamp(date_format)
    return unix_time

def len_bytes(data):
    #calculates the length of base64 string in bytes. If string is empty - returns 'N\A'
    try:
        return(int(len(base64.b64decode(data).hex())/2))
    except:
        #print(data)
        return('N\A')

def to_int(data):
    #converts any data to int, if none - returns "N\A"
    try:
        return(int(data))
    except:
        #print(data)
        return('N\A')

def estimate_inner_delay(dict, pl_size, SF, BW=125):
    
    # inner delay, i.e. LoPy4 delay required to process the next packet up before emission
    
    gen_delay = dict[SF]
    inner_delay = round((gen_delay.predict(np.array([[pl_size]]))[0][0] - calc_ToA(pl_size, SF, BW)/1000), 3)
    #print("estimated inner delay for payload", pl_size, "bytes", "of SF", SF, inner_delay, "seconds")
    return inner_delay


def prepare_dataset(csv_file, gateway_id):
    #dict for inner delay estimation
    dict = {7:pickle.load(open('inner_delay_regression/7.sav', 'rb')), 8:pickle.load(open('inner_delay_regression/8.sav', 'rb')), 9:pickle.load(open('inner_delay_regression/9.sav', 'rb')), 10:pickle.load(open('inner_delay_regression/10.sav', 'rb')), 11:pickle.load(open('inner_delay_regression/11.sav', 'rb')), 12:pickle.load(open('inner_delay_regression/12.sav', 'rb'))}



    # main script
    # load csv
    #csv_file = str(sys.argv[1])
    date = csv_file.split('.')[0]
    #gateway_id = str(sys.argv[2])
    df = pd.read_csv("dataset/"+csv_file)



    # convert date and time to unix ts and starts counting from 0.000 seconds
    df['time'] = df['time'].apply(convert_to_unix_ts)
    df = df.sort_values(by='time')
    df = df.reset_index(drop=True)
    print(df.head())
    df['time'] = df['time'] - df['time'][0]

    # replace the actual physical payload by its size in bytes
    df['physical_payload'] = df['physical_payload'].apply(len_bytes)
    df = df.rename(columns={'physical_payload': 'payload_size'})

    #leaving only data for a specific gateway
    df = df[df.gateway == gateway_id]

    #df = df[df.gateway == "00800000a0001914"]
    #df = df[df.gateway == "00000f0c22433141"]
    #df = df[df.gateway == "7276ff002e062804"]

    # create a new dataset with needed columns only
    out_df = df[['time', 'device_address', 'payload_size', 'frequency', 'spreading_factor', 'mtype', 'fport']]
    print(out_df)

    #clear the received dataset from any false data and conversting values to the right format
    out_df = out_df[out_df.payload_size != 'N\A']
    out_df = out_df[out_df.device_address != '-1']
    out_df = out_df[out_df.fport != '']
    out_df['spreading_factor'] = out_df['spreading_factor'].apply(int)
    out_df['fport'] = out_df['fport'].apply(to_int)
    out_df = out_df[out_df.fport != 'N\A']
    downlink_df = out_df[(out_df.mtype == 11)|(out_df.mtype == 101)]
    #downlink_df.to_csv("dl_"+date+".csv")
    out_df = out_df[out_df.mtype != 101]
    out_df = out_df[out_df.mtype != 11]
    out_df = out_df[out_df.mtype != 110]
    out_df = out_df[out_df.mtype != 111]

    #dropping false devaddr

    out_df['devaddr_len'] = out_df.device_address.apply(len)
    out_df = out_df[out_df.devaddr_len == 8]

    out_df = out_df[out_df["device_address"].str.contains(r'[@#&$%+-/*]') == False]

    out_df = out_df.drop(columns=['devaddr_len'])


    #dropping duplicates
    out_df = out_df.drop_duplicates()

    #adding column with time differences between neighbouring rows
    out_df['wait'] = out_df['time'].shift(-1) - out_df['time']
    #frop faulty duplicated values (same packets which came at the same time which is impossible)
    out_df = out_df[(out_df['wait'] > 0.0000000001)&(out_df['device_address'].shift(-1) != out_df['device_address'])]
    out_df['wait'] = out_df['time'].shift(-1) - out_df['time']

    #dropping tail as it has no wait time
    out_df.drop(out_df.tail(1).index, inplace=True)



    #adding ToA columns and estimated wait time columns
    out_df['payload_size'] = out_df['payload_size'].astype(float)
    out_df['spreading_factor'] = out_df['spreading_factor'].astype(float)
    print(out_df)
    out_df['ToA'] = out_df.apply(lambda x: round(calc_ToA(x.payload_size-13, x.spreading_factor,125)/1000, 3), axis=1)
    

    out_df['estimated_delay'] = out_df.apply(lambda x: estimate_inner_delay(dict, x.payload_size-13, x.spreading_factor), axis=1)

    out_df = out_df.reset_index(drop=True)
    print(out_df)


    #reset index as a lot of rows have been deleted
    out_df = out_df.reset_index(drop=True)

    # Printing the first  rows for testing purposes. Saving the edited dataset to a new csv file.
    print(out_df.head())
    out_df.to_csv("ul_"+date+".csv", index=False)

if __name__=='__main__':
    csv_file = str(sys.argv[1])
    gateway_id = str(sys.argv[2])
    prepare_dataset(csv_file, gateway_id)