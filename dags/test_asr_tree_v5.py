import os
import datetime as dt
import json

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.hooks.postgres_hook import PostgresHook

from tasks.helpers import change_segment_id, create_dir_if_not_exists, parse_json
from tasks.resample import get_resample_task
from tasks.vad import get_vad_task
from tasks.decoder import get_decoder_task
from tasks.move_input import get_move_input_task
from tasks.dia import get_dia_task
from tasks.decoder_post_processing import get_decoder_post_processing_task

RESAMPLE = 'resample'
VAD = 'vad'
DECODER = 'decoder'
DUMMY = 'dummy'
DIA = 'diarization'
DECODER_POST_PROCESSING = 'decoder_post_processing'
CURRENT_VERSION = '0.0.4'

default_args = {
        'owner': 'me',
        'start_date': dt.datetime.utcnow() - dt.timedelta(days=22),
        'retries': 2,
        'retry_delay': dt.timedelta(minutes=5),
}

def process_records():
    # We will keep the records of the last 2 days. As soon as the dag becomes
    # older than 2 days, its dag will not be returned and the pipeline cannot
    # be seen again.
    days_threshold = 30
    date_threshold = (dt.date.today() - dt.timedelta(days_threshold)).isoformat()
    select_sql = "SELECT id, recording_id, pipeline_id, pipeline, created_at from metadata_registry where created_at > \
    '{}' AND NOT status and version = '{}'".format(date_threshold, CURRENT_VERSION)

    pg_hook = PostgresHook(postgres_conn_id='watcher')
    connection = pg_hook.get_conn()

    print("Checking for records in the last %d days" % days_threshold)

    cursor = connection.cursor()
    cursor.execute(select_sql)
    sql_results = cursor.fetchall()
    for result in sql_results:
        print(result)

    return sql_results

def get_task_by_id(task_id, dag):
    for task in dag.tasks:
        if task.task_id == task_id:
            return task

    return None

def get_dummy_task(session_num, dag):
    return DummyOperator(task_id='dummy_%s' % session_num, dag=dag)

def get_task_by_type(step_id, task_type, inputs, parent_ids, session_num, session_metadata, parent_output_dir,
        file_id, recording_id, dag):

    if task_type == RESAMPLE:
        mic_name = inputs['mic_name']
        mic_metadata = session_metadata[mic_name]
        return get_resample_task(mic_name, mic_metadata, session_num, dag,
                parent_output_dir, file_id, recording_id)
    elif task_type == VAD:
        mic_name = inputs['mic_name']
        return get_vad_task(session_num, mic_name, dag)
    elif task_type == DECODER:
        return get_decoder_task(step_id, session_num, session_metadata, inputs, parent_output_dir, file_id, dag)
    elif task_type == DUMMY:
        return get_dummy_task(session_num, dag)
    elif task_type == DIA:
        mic_name = inputs['mic_name']
        speaker_id = inputs['speaker_id']
        return get_dia_task(session_num, mic_name, file_id, speaker_id, dag)
    elif task_type == DECODER_POST_PROCESSING:
        return get_decoder_post_processing_task(session_num, parent_output_dir, file_id, parent_ids, dag)
        
dag1 = DAG('db_record_processing_v04',
          default_args=default_args,
          schedule_interval = '*/1 * * * *')

op = DummyOperator(task_id='dummy', dag=dag1)
t_process_records = PythonOperator(task_id='process_records',
                                   python_callable=process_records,
                                   dag=dag1)

metadata_record_list = process_records()

for metadata_id, recording_id, pipeline_id, pipeline_info, created_at in metadata_record_list:
    metadata = pipeline_info['metadata']
    file_id = "%s-%s" % (recording_id, pipeline_id)
    parent_output_dir = "output/%s/%s" % (recording_id, pipeline_id)
    
    for session_num in pipeline_info['steps']:
        session_num = int(session_num)
        session_metadata = metadata['session'][session_num - 1]
        dag2_id = '%s_session_%d' % (file_id, session_num) 
        dag2 = DAG(
                dag2_id,
                default_args=default_args,
                schedule_interval='@once')

        steps = pipeline_info['steps'][str(session_num)]
        
        step_tasks = {} 
        for step in steps:
            step_info = steps[step]
            step_task = get_task_by_type(
                    step,
                    step_info['task_type'],
                    step_info['inputs'],
                    step_info.get('parent_id', None),
                    session_num,
                    session_metadata,
                    parent_output_dir,
                    file_id,
                    recording_id,
                    dag2)
            step_tasks[int(step)] = step_task
            
            parent_ids = step_info.get('parent_id', None)
            if parent_ids:
                for parent_id in parent_ids:
                    step_task.set_upstream(step_tasks[parent_id])

        globals()[dag2_id] = dag2
