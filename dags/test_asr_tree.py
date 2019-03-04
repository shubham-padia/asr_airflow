import os
import errno
import subprocess
import datetime as dt
import shutil
import json

from shutil import copyfile
from pathlib import Path
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.hooks.postgres_hook import PostgresHook

from tasks.helpers import change_segment_id, create_dir_if_not_exists
from tasks.resample import get_resample_task
from tasks.vad import get_vad_task
from tasks.decoder import get_decoder_task

RESAMPLE = 'resample'
VAD = 'vad'
DECODER = 'decoder'
DUMMY = 'dummy'

default_args = {
        'owner': 'me',
        'start_date': dt.datetime.utcnow() - dt.timedelta(days=22),
        'retries': 2,
        'retry_delay': dt.timedelta(minutes=5),
}

def move_input_task(**kwargs):
    params = kwargs['params']
    session_metadata = params['session_metadata']
    parent_output_dir = params['parent_output_dir']

#    for attr in dir(obj):
#        print("obj.%s = %r" % (attr, getattr(obj, attr)))

    current_dir = os.getcwd()
    target_dir = "%s/moved_input/%s" % (current_dir, parent_output_dir)
            
    create_dir_if_not_exists(target_dir)
 
    for mic_name in session_metadata:
        # copy to json_id/raw/
        file_path = session_metadata[mic_name]['filename']
        file_name = os.path.basename(file_path)
#           print(file_name)
        src = current_dir + '/' + file_path
        dst = target_dir + '/' + file_name
        shutil.copyfile(src, dst)

def process_records():
    # We will keep the records of the last 2 days. As soon as the dag becomes
    # older than 2 days, its dag will not be returned and the pipeline cannot
    # be seen again.
    days_threshold = 30
    date_threshold = (dt.date.today() - dt.timedelta(days_threshold)).isoformat()
    select_sql = "SELECT id, filename, created_at from metadata_registry where created_at > \
    '{}' AND NOT status".format(date_threshold)

    pg_hook = PostgresHook(postgres_conn_id='watcher')
    connection = pg_hook.get_conn()

    print("Checking for records in the last %d days" % days_threshold)

    cursor = connection.cursor()
    cursor.execute(select_sql)
    sql_results = cursor.fetchall()
    for result in sql_results:
        print(result)

    return sql_results

def parse_metadata(metadata_file_path):
    metadata = None 
    with open(metadata_file_path, "r") as stream:
        try:
            metadata = json.loads(stream.read())
        except ValueError as exc:
            print(exc)
    
    return metadata

def get_task_by_id(task_id, dag):
    for task in dag.tasks:
        if task.task_id == task_id:
            return task

    return None

def get_dummy_task(session_num, dag):
    return DummyOperator(task_id='dummy_%s' % session_num, dag=dag)



def get_task_by_type(task_type, inputs, session_num, session_metadata, parent_output_dir,
        pipeline_name, dag):

    if task_type == RESAMPLE:
        mic_name = inputs['mic_name']
        mic_metadata = session_metadata[mic_name]
        return get_resample_task(mic_name, mic_metadata, session_num, dag,
                parent_output_dir, pipeline_name)
    elif task_type == VAD:
        mic_name = inputs['mic_name']
        return get_vad_task(mic_name, session_num, pipeline_name, dag)
    elif task_type == DECODER:
        return get_decoder_task(session_num, inputs, parent_output_dir, dag)
    elif task_type == DUMMY:
        return get_dummy_task(session_num, dag)

dag1 = DAG('db_record_processing_v04',
          default_args=default_args,
          schedule_interval = '*/1 * * * *')

op = DummyOperator(task_id='dummy', dag=dag1)
t_process_records = PythonOperator(task_id='process_records',
                                   python_callable=process_records,
                                   dag=dag1)

metadata_record_list = process_records()

for metadata_id, file_path, created_at in metadata_record_list:
    created_at_str = created_at.strftime("%Y_%m_%d_%I_%M_%S")
    pipeline_info = parse_metadata(file_path)

    if pipeline_info.get('steps', None):
        metadata = pipeline_info['metadata']
        pipeline_name = os.path.splitext(os.path.basename(file_path))[0]
        parent_output_dir = "output/%s/%s" % (pipeline_name, created_at_str)
        
        for session_num in pipeline_info['steps']:
            session_num = int(session_num)
            session_metadata = metadata['session'][session_num - 1]
            dag2_id = 'atree_%s_session_%d' % (pipeline_name, session_num) 
            dag2 = DAG(
                    dag2_id,
                    default_args=default_args,
                    schedule_interval='@once')

            t_move_input_task = PythonOperator(
                task_id='move_input',
                dag=dag2,
                python_callable=move_input_task,
                params={
                    "parent_output_dir": parent_output_dir,
                    "session_metadata": session_metadata
                },
                provide_context=True
            )

            steps = pipeline_info['steps'][str(session_num)]
            
            step_tasks = {} 
            for step in steps:
                step_info = steps[step]
                print(step_info)
                step_task = get_task_by_type(
                        step_info['task_type'],
                        step_info['inputs'],
                        session_num,
                        session_metadata,
                        parent_output_dir,
                        pipeline_name,
                        dag2)
                step_tasks[int(step)] = step_task
                
                parent_ids = step_info.get('parent_id', None)
                if parent_ids:
                    for parent_id in parent_ids:
                        print(parent_id)
                        print(step_tasks)
                        step_task.set_upstream(step_tasks[parent_id])

            globals()[dag2_id] = dag2

