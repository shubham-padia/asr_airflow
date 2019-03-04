import os
import subprocess

from airflow.operators.python_operator import PythonOperator
from tasks.helpers import create_dir_if_not_exists, change_segment_id

def decoder_task(**kwargs):
    params = kwargs['params']
    seg = params['seg']
    wav = params['wav']
    seg_hybrid = seg['hybrid']
    wav_hybrid = wav['hybrid']
    seg_mic_name = seg_hybrid['mic_name']
    wav_mic_name = wav_hybrid['mic_name']
    seg_speaker_id = seg_hybrid['speaker_id']
    wav_speaker_id = wav_hybrid['speaker_id']
    seg_task_id = "vad_%s" % seg_mic_name
    wav_task_id = "vad_%s" % wav_mic_name

    ti = kwargs['ti']
    seg_data = ti.xcom_pull(task_ids=seg_task_id)
    wav_data = ti.xcom_pull(task_ids=wav_task_id)
    
    output_prefix = "session%s-%s-seg-%s-wav-%s" % (params['session_num'],
            seg_speaker_id, seg_mic_name, wav_mic_name)
    output_dir = "%s/%s/session%d/hybrid/decoder/%s" % (os.getcwd(),
            params['parent_output_dir'], params['session_num'], output_prefix) 
    create_dir_if_not_exists(output_dir)
    
    
    # The decode bash script requires the segment file name and the wav
    # file name to be the same. We are using symlinks to make them have the
    # same file name. They also need to be in the same directory.
    seg_file = "%s/%s-session%s-%s-%s.seg" % (seg_data[0], seg_data[2],
            params['session_num'], seg_mic_name, seg_speaker_id)
    wav_file = "%s/%s-session%s-%s-%s.wav" % (wav_data[0],
            wav_data[2], params['session_num'], wav_mic_name,
            wav_speaker_id)
    
    symlink_dir = "%s/input-symlinks" % (output_dir)
    symlink_prefix = "%s/%s" % (symlink_dir, output_prefix)
    symlink_wav_file = "%s.wav" % symlink_prefix
    symlink_seg_file = "%s.seg" % symlink_prefix

    create_dir_if_not_exists(symlink_dir)
    os.symlink(wav_file, symlink_wav_file)
    change_segment_id(seg_file, symlink_seg_file)

    print("output_dir: %s" % output_dir)
    print("%s" % symlink_seg_file)
    print("%s" % symlink_wav_file)
    
    decoder_dir = '/home/shubham/backend_asr/lvscr_ntu/lvcsr-170923-v2/scripts'
    decoder_script = 'decoding_stdl.sh'
    
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    decoder_command = ['bash', decoder_script,
            '../systems', symlink_seg_file, symlink_wav_file, output_dir,
            output_prefix]
    subprocess.check_call(decoder_command, env=my_env, cwd=decoder_dir)

def get_decoder_task(session_num, hybrid, parent_output_dir, dag):
    seg_hybrid = hybrid['seg']
    wav_hybrid = hybrid['wav']

    t_decoder = PythonOperator(task_id='hybrid_seg_%s_wav_%s' % 
            (seg_hybrid['mic_name'], wav_hybrid['mic_name']),
            dag=dag,
            params={
                "session_num": session_num,
                "parent_output_dir": parent_output_dir,
                "seg": {
                    "hybrid": seg_hybrid
                },
                "wav": {
                    "hybrid": wav_hybrid
                }
            },
            python_callable=decoder_task,
            provide_context=True
        )

    return t_decoder