import os
import subprocess
from tasks.helpers import create_dir_if_not_exists
from tasks.audio_to_video import convert_audio_to_video
from airflow.operators.python_operator import PythonOperator

def resample(channels, input_file_name, output_prefix):
    wav_list = []
    for idx, channel in enumerate(channels):
        output_file_name = output_prefix + '-' + str(idx + 1) + '.wav'
        wav_list.append(output_file_name)
        resample_command = ["sox", input_file_name, "-r16k", "-b16",
        output_file_name, "remix", str(channel)]
        subprocess.run(resample_command)

    return wav_list

def resample_task(**kwargs):
    params = kwargs['params']
    file_metadata = params['metadata']
    mic_name = params['mic_name']
    session_num = params['session_num']
    file_id = params['file_id']

    input_file_name = 'data/' + params['recording_id'] + '/' + file_metadata['filename']
    channels = file_metadata['channels']
    file_dir = '%s/%s/session%d/%s' % (os.getcwd(), params['parent_output_dir'],
            session_num,
            mic_name)
    output_dir = file_dir + '/0_raw'
    create_dir_if_not_exists(output_dir)
    
    output_prefix = '%s/%s-session%d-%s' % (output_dir, file_id, session_num,
            mic_name)

    
    wav_list = resample(channels, input_file_name, output_prefix)
    
    video_file_name_prefix = "%s-session%d-%s" % (file_id, session_num,
            mic_name)
    video_dir = file_dir + '/3_video'
    create_dir_if_not_exists(video_dir)
    convert_audio_to_video(wav_list, video_file_name_prefix, video_dir)

    return {
            'task_type': resample,
            'output_dir': output_dir,
            'file_id': file_id,
            'file_dir': file_dir
    }

def get_resample_task(mic_name, mic_metadata, session_num, dag,
        parent_output_dir, file_id, recording_id):

    return PythonOperator(
        task_id='resample_%s' % mic_name, 
        python_callable=resample_task,
        params={
            "session_num": session_num,
            "mic_name": mic_name,
            "metadata": mic_metadata,
            "parent_output_dir": parent_output_dir,
            "file_id": file_id,
            "recording_id": recording_id
        },
        dag=dag,
        provide_context=True)
