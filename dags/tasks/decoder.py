import os
import subprocess

from airflow.operators.python_operator import PythonOperator
from tasks.helpers import create_dir_if_not_exists, change_segment_id
from envparse import env
from tasks.convert_stm_to_srt import convert_stm_to_srt


def get_decoder_location(lang):
    env.read_envfile()
    if lang == 'sge':
        decoder_dir = env('SGE_DECODER_DIR')
        decoder_script = env('SGE_DECODER_SCRIPT')
    elif lang == 'cs':
        decoder_dir = env('CS_DECODER_DIR')
        decoder_script = env('CS_DECODER_SCRIPT')
    elif lang == 'ml':
        decoder_dir = env('ML_DECODER_DIR')
        decoder_script = env('ML_DECODER_SCRIPT')

    return decoder_dir, decoder_script


def decoder_task(**kwargs):
    params = kwargs['params']
    seg = params['seg']
    wav = params['wav']
    seg_hybrid = seg['hybrid']
    wav_hybrid = wav['hybrid']
    seg_mic_name = seg_hybrid['mic_name']
    wav_mic_name = wav_hybrid['mic_name']
    seg_source = seg_hybrid.get('source', 'vad')
    wav_source = wav_hybrid.get('source', 'vad')
    seg_speaker_id = seg_hybrid['speaker_id']
    wav_speaker_id = wav_hybrid['speaker_id']

    seg_task_id = "%s_%s" % (seg_source, seg_mic_name)
    wav_task_id = "%s_%s" % (wav_source, wav_mic_name)

    if seg_source == 'diarization':
        seg_task_id = "%s_%s" % (seg_task_id, seg_speaker_id)
    if wav_source == 'diarization':
        wav_task_id = "%s_%s" % (wav_task_id, wav_speaker_id)

    ti = kwargs['ti']
    seg_data = ti.xcom_pull(task_ids=seg_task_id)
    wav_data = ti.xcom_pull(task_ids=wav_task_id)

    if seg_mic_name == wav_mic_name:
        output_dir = "%s/%s/session%d/%s/2_decoder" % (os.getcwd(),
                                                       params['parent_output_dir'], params['session_num'], seg_mic_name)
        output_prefix = "%s-session%s-%s-spk-%s" % (params['file_id'], params['session_num'],
                                                    wav_mic_name, wav_speaker_id)
    else:
        output_dir = "%s/%s/session%d/hybrid/decoder" % (os.getcwd(),
                                                         params['parent_output_dir'], params['session_num'])
        output_prefix = "%s-session%s-seg-%s-wav-%s-spk-%s" % (params['file_id'], params['session_num'],
                                                               seg_mic_name, wav_mic_name, wav_speaker_id)

    create_dir_if_not_exists(output_dir)

    # The decode bash script requires the segment file name and the wav
    # file name to be the same. We are using symlinks to make them have the
    # same file name. They also need to be in the same directory.
    seg_file = "%s/%s-session%s-%s-%s.seg" % (seg_data['output_dir'], seg_data['file_id'],
                                              params['session_num'], seg_mic_name, seg_speaker_id)
    wav_file = "%s/%s-session%s-%s-%s.wav" % (wav_data['output_dir'],
                                              wav_data['file_id'], params['session_num'], wav_mic_name,
                                              wav_speaker_id)

    symlink_dir = "%s/input-symlinks" % (output_dir)
    symlink_prefix = "%s/%s" % (symlink_dir, output_prefix)
    symlink_wav_file = "%s.wav" % symlink_prefix
    symlink_seg_file = "%s.seg" % symlink_prefix

    create_dir_if_not_exists(symlink_dir)
    try:
        os.symlink(wav_file, symlink_wav_file)
    except OSError:
        print("File exists, skipping symlink creation")

    if not os.path.exists(symlink_seg_file):
        change_segment_id(seg_file, symlink_seg_file)

    decoder_dir, decoder_script = get_decoder_location(params['lang'])

    my_env = os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    decoder_command = ['bash', decoder_script,
                       '../systems', symlink_seg_file, symlink_wav_file, output_dir,
                       output_prefix]
    subprocess.check_call(decoder_command, env=my_env, cwd=decoder_dir)

    stm_path =  "%s/%s.stm" % (output_dir, output_prefix)
    srt_path =  "%s/%s.srt" % (output_dir, output_prefix)
    convert_stm_to_srt(stm_path, srt_path)
    
    ti.xcom_push(key='decoder_srt_%s' % params['step_id'], value=srt_path)

def get_decoder_task(step_id, session_num, session_metadata, hybrid, parent_output_dir, file_id, dag):
    seg_hybrid = hybrid['seg']
    wav_hybrid = hybrid['wav']
    lang = session_metadata[wav_hybrid['mic_name']]['lang']
    task_id = 'decoder_%s_seg_%s_%s_wav_%s_%s' % (seg_hybrid['source'],
                                          seg_hybrid['mic_name'], seg_hybrid['speaker_id'],
                                          wav_hybrid['mic_name'], wav_hybrid['speaker_id'])
    
    if seg_hybrid['mic_name'] != wav_hybrid['mic_name']:
        task_id = "hybrid_%s" % task_id

    t_decoder = PythonOperator(task_id=task_id,
                               dag=dag,
                               params={
                                   "step_id": step_id,
                                   "session_num": session_num,
                                   "parent_output_dir": parent_output_dir,
                                   "seg": {
                                       "hybrid": seg_hybrid
                                   },
                                   "wav": {
                                       "hybrid": wav_hybrid
                                   },
                                   "file_id": file_id,
                                   "lang": lang
                               },
                               python_callable=decoder_task,
                               provide_context=True
                               )

    return t_decoder
