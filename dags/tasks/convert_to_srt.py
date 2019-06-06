import os
from tasks.convert_stm_to_srt import convert_stm_to_srt
from tasks.combine_multi_channel_transcript import combine_transcripts

def bulk_convert_stm_to_srt(input_stm_list, output_location):
    srt_list = []
    for stm_file in input_stm_list:
        output_file_name = os.path.splitext(os.path.basename(stm_file))[0]
        output_path = output_location + '/' + output_file_name
        srt_list += output_path
        convert_stm_to_srt(stm_file, output_path)

    return srt_list

def convert_to_srt(input_stm_list, output_location):
    srt_list = bulk_convert_stm_to_srt(input_stm_list, output_location)
    combine_transcripts(srt_list, output_srt_path)
