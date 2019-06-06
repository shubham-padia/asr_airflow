# ================================================================================================================ #
# This script combines the transcripts of the multiple channels of the single media file into one complete srt file 					   #
# Input  : chn1 srt file, chn2 srt file, chnX srt file													 					   #
# Output : path to a complete srt file 															 					   #
# Usage  : ./combine_multich_Transcript.py <ch1.srt> <ch2.ctm> <...srt> <path-to-output.srt>								   #
# Author : Zin																									   #
# ================================================================================================================ #

import os
import sys
import difflib
from pprint import pprint
from itertools import islice

# ================================================================================================================ #


def readSRT(srtFile, google_list, chnID, fid):
    print('==> reading srt')
    #google_list = []
    google_dict = {}
    color_code = ["#3f5ea0", "#9d5e2d", "#339bbe", "#d85f7f",
                  "#c96eae", "#637ee2", "#844bbe", "#3302c0", "#d305a4"]

    #	code here	#
    with open(srtFile, 'r') as f:
        while True:
            google_dict = {}
            next_n_lines = list(islice(f, 4))

            if next_n_lines:
                sid = next_n_lines[0]
                timeinfo = next_n_lines[1].split('-->')
                textLV = next_n_lines[2]
                google_dict['sid'] = sid.strip()
                google_dict['start'] = timeinfo[0].strip()
                google_dict['end'] = timeinfo[1].strip()
                google_dict['textLV'] = "<font color='" + color_code[chnID] + \
                    "'>Ch"+str(chnID)+"-</font>"+textLV.strip()
                google_dict['textLV'] = resizeFont(google_dict['textLV'])
                google_dict['timeinfo'] = next_n_lines[1].strip()
                google_dict['endmili'] = srtTimeToMili(google_dict['end'])
                google_dict['startmili'] = srtTimeToMili(google_dict['start'])

                google_list.append(google_dict)

            if not next_n_lines:
                break

    print('==> reading srt done')
    return google_list

# ================================================================================================================ #


def readSRTMulti(srtFile, google_list, chnID, chn_len):
    print('==> reading srt')
    google_dict = {}

    color_code = ["#3f5ea0", "#9d5e2d", "#339bbe", "#d85f7f",
                  "#c96eae", "#637ee2", "#844bbe", "#3302c0", "#d305a4"]

    #	code here	#
    with open(srtFile, 'r') as f:
        while True:
            google_dict = {}
            google_dict['textYT'] = {}
            google_dict['textLV'] = {}
            next_n_lines = list(islice(f, 4))

            if next_n_lines:
                sid = next_n_lines[0]
                timeinfo = next_n_lines[1].split('-->')
                textLV = next_n_lines[2]
                google_dict['sid'] = sid.strip()
                google_dict['start'] = timeinfo[0].strip()
                google_dict['end'] = timeinfo[1].strip()
                # insert subs for all channel
                for i in range(1, chn_len+1):
                    if (i == chnID):
                        # add sub
                        google_dict['textLV'][chnID] = "<font color='" + \
                            color_code[chnID] + "'>Ch" + \
                            str(chnID)+"-</font>"+textLV.strip()
                    else:
                        # empty sub
                        google_dict['textLV'][i] = "<font color='" + \
                            color_code[i] + "'>Ch"+str(i)+"-</font>"
                # google_dict['textLV']=resizeFont(google_dict['textLV'])
                google_dict['timeinfo'] = next_n_lines[1].strip()
                google_dict['endmili'] = srtTimeToMili(google_dict['end'])
                google_dict['startmili'] = srtTimeToMili(google_dict['start'])

                google_list.append(google_dict)

            if not next_n_lines:
                break

    print('==> reading srt done')
    return google_list

# ================================================================================================================ #


def resizeFont(subtext):
    font_size = "46"
    return "<font size='" + font_size + "'>" + subtext + "</font>"


def formatDict(g_dict):
    for idx, val in enumerate(g_dict):
        try:
            if (g_dict[idx]['endmili'] > g_dict[idx+1]['startmili']):
                g_dict[idx]['endmili'] = g_dict[idx+1]['startmili']
                g_dict[idx]['end'] = g_dict[idx+1]['start']
        except:
            # indx out-of-bound error when idx=last index
            continue

    return g_dict
# ================================================================================================================ #


def srtTimeToMili(timeinfo):
    time = timeinfo.split(':')
    hrs = int(time[0])
    mins = int(time[1])
    secs = int(time[2].split(',')[0])
    milis = int(time[2].split(',')[1])

    totalmilis = (hrs*60*60*1000) + (mins*60*1000) + (secs * 1000) + milis

    return totalmilis

# ================================================================================================================ #


def writeResults(google_list, outFile, mode):
    print('==> write google and lvcsr comparison sentences into text file')
    pprint(len(google_list))
    with open(outFile, 'w') as f:
        for idx, item in enumerate(google_list):

            f.write(str(idx+1) + '\n')
            f.write(item['start'] + ' --> ' + item['end'] + '\n')
            f.write(item['textLV']+'\n\n')
            # f.write("<font color='#1ABB12'>OurSys: </font>"+ textdiff +'\n\n')

    print('==> write google and lvcsr comparison sentences into text file done')

# ================================================================================================================ #
def writeResultsMulti(google_list, outFile, mode, chn_len):
    print('==> write google and lvcsr comparison sentences into text file')
    pprint(len(google_list))
    with open(outFile, 'w') as f:
        for idx, item in enumerate(google_list):

            f.write(str(idx+1) + '\n')
            f.write(item['start'] + ' --> ' + item['end'] + '\n')
            for i in range(1, chn_len+1):
                f.write(item['textLV'][i]+'\n')
            f.write('\n')
            # f.write("<font color='#1ABB12'>OurSys: </font>"+ textdiff +'\n\n')

    print('==> write google and lvcsr comparison sentences into text file done')


# ================================================================================================================ #

def combine_transcripts(srt_array, srtout):

    channel_len = len(srt_array)
    outfile = srtout
    mode = '1'
    multi_chn_sub = False
    print(srt_array)

    # call procedures
    if not multi_chn_sub:
        print('single sub line for for YT and LVCSR')
        glist = []
        for idx, srt_file in enumerate(srt_array):
            fid = os.path.splitext(os.path.basename(srt_file))[0]
            # sys.exit(0)
            print('==> Processing {} srt file'.format(srt_file))
            glist = readSRT(srt_file, glist, idx+1, fid)
        newlist = sorted(glist, key=lambda k: k['startmili'])
        #newlist = formatDict(newlist)
        writeResults(newlist, outfile, mode)
    if multi_chn_sub:
        print('produced multi-lines subititle of each channel for YT and LVCSR')
        glist = []
        for idx, srt_file in enumerate(srt_array):
            print('==> Processing {} srt file'.format(srt_file))
            glist = readSRTMulti(srt_file, glist, idx+1, channel_len)
        newlist = sorted(glist, key=lambda k: k['startmili'])
        newlist = formatDict(newlist)
        writeResultsMulti(newlist, outfile, mode, channel_len)
