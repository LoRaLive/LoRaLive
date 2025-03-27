import math

def calc_ToA(size, SF, BW, coding_rate='4/5', low_DR_opt='auto', expl_header=True, preamble_len=8):
    # based on https://github.com/avbentem/airtime-calculator/blob/master/src/lora/Airtime.ts
    size = size + 13
    t_sym = (math.pow(2, SF) / (BW*1000)) * 1000
    t_preamble = (preamble_len + 4.25) * t_sym
    if expl_header == True:
        H = 0
    else:
        H = 1

    if (low_DR_opt == 'auto' and BW == 125 and SF >= 11) or (low_DR_opt == True):
        DE = 1
    else:
        DE = 0

    CR = int(coding_rate[2]) - 4

    payload_symb = (8 + 
    max(
        math.ceil((8 * size - 4 * SF + 28 + 16 - 20 * H) / (4 * (SF - 2 * DE))) * (CR + 4), 
        0 ) 
        )
    t_payload = payload_symb * t_sym

    return t_preamble + t_payload