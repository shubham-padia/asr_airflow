import os

from airflow.operators.python_operator import PythonOperator
from tasks.combine_multi_channel_transcript import combine_transcripts
from tasks.helpers import create_dir_if_not_exists

def decoder_post_processing_task(**kwargs):
    params = kwargs['params']
    parent_ids = params['parent_ids']
    
    ti = kwargs['ti']
    srt_list = []
    for parent_id in parent_ids:
        srt_list.append(ti.xcom_pull(key='decoder_srt_%s' % parent_id, task_ids=None))

    output_dir = "%s/%s/session%d/srt/" % (os.getcwd(), params['parent_output_dir'], params['session_num'])
    create_dir_if_not_exists(output_dir)
    output_srt_path = "%s/%s-session%s.srt" % (output_dir, params['file_id'], params['session_num'])

    combine_transcripts(srt_list, output_srt_path)

def get_decoder_post_processing_task(session_num, parent_output_dir, file_id, parent_ids, dag):
    task_id = "decoder_post_processing_%s" % session_num

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
