import math
import pandas as pd
import sys
#from estimate import estimate_inner_delay
from utils import calc_ToA
import numpy as np
import pickle
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import os
#from memory_profiler import profile
import psutil
import time

def estimate_inner_delay(dict, pl_size, SF, BW=125):
    
    # inner delay, i.e. LoPy4 delay required to process the next packet up before emission
    
    gen_delay = dict[SF]
    inner_delay = round((gen_delay.predict(np.array([[pl_size]]))[0][0] - calc_ToA(pl_size, SF, BW)/1000), 3)
    #print("estimated inner delay for payload", pl_size, "bytes", "of SF", SF, inner_delay, "seconds")
    return inner_delay

def recalculate_wait_time(df):
    #adding column with time differences between neighbouring rows
    df['wait'] = df['time'].shift(-1) - df['time']
    df = df[(df['wait'] > 0.01)]
    df['wait'] = df['time'].shift(-1) - df['time']

    df = df.reset_index(drop=True)
    return df

def split_df_wait(df, delta):
    df_new = df.iloc[0:0]
    length = len(df)
    for i in range (0, length):
        try:
            k = 1
            wait = df['wait'].iloc[i]
            estimated_delay = df['estimated_delay'].iloc[i] + df['ToA'].iloc[i+1] + delta
            if wait < estimated_delay:
                while wait < estimated_delay:
                    j = i+k
                    wait += df['wait'].iloc[j]
                    df_new = df_new._append(df.iloc[j])
                    k += 1
                for j in range(i+1, i+k):
                    df = df.drop(index=j)
                length = len(df)
            df_new = df_new.reset_index(drop=True)     
            df = df.reset_index(drop=True)
            #print("iteration", i)
        except:
            #print("exception on iteration", i)
            pass
    
    df = recalculate_wait_time(df)
    print("old")
    print(df)
    print("new")
    df_new = recalculate_wait_time(df_new)
    print(df_new)
    return (df, df_new)

def split_csv_wait(df, delta):
    df_wait = []
    while len(df) > 0:
        df, df_new = split_df_wait(df, delta)
        df_wait._append(df)
        #df_split_array.append(df_new)
        df = df_new
    return df_wait




#@profile
def split_csv_by_device(dataset, dc_limit=36, delta=0):
    df = pd.read_csv(dataset)
    #dev_number = split_csv_wait(df, delta)
    dev_number = [df]
    print(dev_number)
    print("length of each split csv by wait time:")
    for i in dev_number:
        print(len(i))
    dev_number = len(dev_number)
    devices_df = []
    sum = []
    last_ts = []

    for i in range(0, dev_number):
        devices_df.append(df[0:0])
        sum.append([0,0])
        last_ts.append([0,0])

    for i in range(0, len(df)):
        #print(sum)
        #print("row number", i)
        k = i
        next_row = df.iloc[k]
        placed = False
        counter = 0
        while not placed == True:
            current_row = devices_df[k%len(devices_df)][-1:]
            #print(len(current_row))
            if len(current_row) == 0:
                devices_df[k%len(devices_df)] = devices_df[k%len(devices_df)]._append(next_row)
                placed = True
                if next_row['frequency'] <= 868000000:
                    sum[k%len(devices_df)][0] += next_row['ToA']
                else:
                    sum[k%len(devices_df)][1] += next_row['ToA']
            else:
                current_row = current_row.iloc[-1]
                #print(devices_df[k%len(devices_df)]['time'].iloc[-1])
                #print(current_row['estimated_delay']+next_row['ToA'])
                #print(next_row['time']-current_row['time'])
                if (current_row['estimated_delay']+next_row['ToA']+delta<next_row['time']-current_row['time']):
                    #print("diff", (next_row['time'] - last_ts[k%len(devices_df)][0]))
                    #print("sum", sum[k%len(devices_df)][0])
                    if (next_row['frequency'] <= 868000000)and(sum[k%len(devices_df)][0]<dc_limit):
                        #and((sum[k%len(devices_df)][0]<36)or(sum[k%len(devices_df)][1]<36))):
                        devices_df[k%len(devices_df)] = devices_df[k%len(devices_df)]._append(next_row)
                        sum[k%len(devices_df)][0] += next_row['ToA']
                        if sum[k%len(devices_df)][0] > dc_limit:
                            last_ts[k%len(devices_df)][0] = next_row['time']
                        placed = True
                    elif (next_row['frequency'] > 868000000)and(sum[k%len(devices_df)][1]<dc_limit):
                        
                        #and((sum[k%len(devices_df)][0]<36)or(sum[k%len(devices_df)][1]<36))):
                        devices_df[k%len(devices_df)] = devices_df[k%len(devices_df)]._append(next_row)
                        sum[k%len(devices_df)][1] += next_row['ToA']
                        if sum[k%len(devices_df)][1] > dc_limit:
                            last_ts[k%len(devices_df)][1] = next_row['time']
                        placed = True
                    elif ((sum[k%len(devices_df)][0]>=dc_limit)and(next_row['frequency'] <= 868000000)and(next_row['time'] - last_ts[k%len(devices_df)][0] > 3600)):
                        #print('success1')
                        devices_df[k%len(devices_df)] = devices_df[k%len(devices_df)]._append(next_row)
                        sum[k%len(devices_df)][0] = next_row['ToA']
                        if sum[k%len(devices_df)][0] > dc_limit:
                            last_ts[k%len(devices_df)][0] = next_row['time']
                        placed = True
                    elif ((sum[k%len(devices_df)][1]>=dc_limit)and(next_row['frequency'] > 868000000)and(next_row['time'] - last_ts[k%len(devices_df)][1] > 3600)):
                        #print("success2")
                        devices_df[k%len(devices_df)] = devices_df[k%len(devices_df)]._append(next_row)
                        sum[k%len(devices_df)][1] = next_row['ToA']
                        if sum[k%len(devices_df)][1] > dc_limit:
                            last_ts[k%len(devices_df)][1] = next_row['time']
                        placed = True
                    else:
                        k += 1
                        counter += 1

                else:
                    k += 1
                    counter += 1
                if (counter == len(devices_df)):
                    devices_df.append(df[0:0])
                    devices_df[-1] =  devices_df[-1]._append(next_row)
                    sum.append([0,0])
                    last_ts.append([0,0])
                    if next_row['frequency'] <= 868000000:
                        sum[-1][0] += next_row['ToA']
                    else:
                        sum[-1][1] += next_row['ToA']
                    placed = True

    print("length of phy dev", len(devices_df))
    s = 0
    for i in devices_df:
        s += len(i)
    print("rows", s)
    print(last_ts)
    #device_dir_name = dataset.split('.')[0]
    device_dir_name = 'devices'
    if not os.path.exists(device_dir_name):
        os.mkdir(device_dir_name)
    for i in range (0, len(devices_df)):
        devices_df[i]['wait'] = devices_df[i]['time'].shift(-1) - devices_df[i]['time']
        devices_df[i]['ToA_shift'] = devices_df[i]['ToA'].shift(-1)
        devices_df[i]['estimated_delay'] = devices_df[i]['estimated_delay'] + devices_df[i]['ToA_shift']
        #df = df.drop(['ToA_shift'], axis=1)
        devices_df[i] = devices_df[i]
        devices_df[i].to_csv(device_dir_name+'/device-'+str(i)+'.csv', index=False )
    return(dev_number, len(devices_df))

if __name__=='__main__':
    dataset = str(sys.argv[1])
    dc_limit = int(sys.argv[2])
    delta = int(sys.argv[3])
    process = psutil.Process(os.getpid())

    # Before
    #cpu_percent_before = process.cpu_percent(interval=0.001)
    #mem_before = process.memory_info().rss / 1024 / 1024  # in MB
    st = time.process_time()
    # Get the CPU percent before the function execution
    before_cpu_percent = psutil.cpu_percent(interval=None)
    
    # Get the current time
    start_time = time.time()
    
    split_csv_by_device(dataset, dc_limit, delta)

    # Get the elapsed time
    elapsed_time = time.time() - start_time
    
    # Get the CPU percent after the function execution
    after_cpu_percent = psutil.cpu_percent(interval=elapsed_time)
    
    # Compute the approximate CPU load caused by the function
    cpu_load = after_cpu_percent - before_cpu_percent

    print("CPU load", cpu_load)

    end = time.process_time()

    cpu_process_time = end-st

    print("CPU process time", cpu_process_time)

    print("elapsed time", elapsed_time)
    