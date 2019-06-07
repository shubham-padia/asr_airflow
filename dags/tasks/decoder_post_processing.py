import os

from airflow.operators.python_operator import PythonOperator
from tasks.combine_multi_channel_transcript import combine_transcripts
from tasks.helpers import create_dir_if_not_exists

def decoder_post_processing_task(**kwargs):
    params = kwargs['params']
    parent_ids = params['parent_ids']
    
    ti = kwargs['ti']
    srt_list = []
    mic_set = set()
    is_hybrid = False

    for parent_id in parent_ids:
        msg = ti.xcom_pull(key='decoder_srt_%s' % parent_id, task_ids=None)
        srt_list.append(msg['srt_path'])
        mic_set.add(msg['wav_mic_name'])
        mic_set.add(msg['seg_mic_name'])
        if msg['is_hybrid']:
            is_hybrid = True

    if not is_hybrid and len(mic_set) == 1:
        mic_name = mic_set.pop()
        output_dir = "%s/%s/session%d/%s/3_video" % (os.getcwd(), params['parent_output_dir'], params['session_num'], mic_name)
        create_dir_if_not_exists(output_dir)
        output_srt_path = "%s/%s-session%d-%s.srt" % (output_dir, params['file_id'], params['session_num'], mic_name)
    else:
        output_dir = "%s/%s/session%d/hybrid/video" % (os.getcwd(), params['parent_output_dir'], params['session_num'])
        create_dir_if_not_exists(output_dir)
        output_srt_path = "%s/%s-session%d-parents-%s.srt" % (output_dir, params['file_id'], params['session_num'], "_".join(str(x) for x in parent_ids))

    combine_transcripts(srt_list, output_srt_path)

def get_decoder_post_processing_task(session_num, parent_output_dir, file_id, parent_ids, dag):
    task_id = "decoder_post_processing_%d_parents_%s" % (session_num, "_".join(str(x) for x in parent_ids))

    t_decoder_post_processing = PythonOperator(task_id=task_id,
                               dag=dag,
                               params={
                                   "session_num": session_num,
                                   "parent_ids": parent_ids,
                                   "parent_output_dir": parent_output_dir,
                                   "file_id": file_id
                               },
                               python_callable=decoder_post_processing_task,
                               provide_context=True
                               )
    
    return t_decoder_post_processing
