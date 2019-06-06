#!/usr/bin/env python
'''
Usage: ./scripty.py <path-to-stm> <path-to-srt>
* stm and srt shared the same name except extension
'''

import sys
from pprint import pprint


def readSTM(stmFile):
    tr_list = []
    with open(stmFile, 'r') as inFile:
        content = inFile.readlines()

    for sent in content:
        tr_dict = {}
        tokens = sent.strip().split(" ")
        tr_dict['txt'] = " ".join(tokens[6:])

        if tr_dict['txt']:
            tr_dict['st'] = tokens[3]
            tr_dict['et'] = tokens[4]
            tr_list.append(tr_dict)

    return tr_list


def getSRTtime(timeval):
    time_sec = int(timeval.split('.')[0])
    time_mili = int(timeval.split('.')[1])
    m, s = divmod(time_sec, 60)
    h, m = divmod(m, 60)
    timev = "%02d:%02d:%02d,%d" % (h, m, s, time_mili * 10)

    return str(timev)


def writeSRT(tr_list, outFile):
    try:
        with open(outFile, 'w') as outF:	
            for idx, val in enumerate(tr_list):
                outF.write( str(idx+1) + '\n' )
                outF.write( getSRTtime(val['st']) + ' --> ' +  getSRTtime(val['et']) + '\n')
                outF.write( val['txt']+ '\n')
                outF.write('\n')
    
        outF.close()
        print("[LOG|INFO] Written SRT file at: {}".format(outFile))
    except IOError:
        print("[LOG|ERROR] Error writing SRT file")
        raise IOError

def convert_stm_to_srt(inSTM, outSRT):
    
    print('\n[LOG|INFO] Input STM: {}\n[LOG|INFO] Output SRT: {}\n'.format(inSTM, outSRT))
    trList = readSTM(inSTM)
    writeSRT(trList, outSRT)
