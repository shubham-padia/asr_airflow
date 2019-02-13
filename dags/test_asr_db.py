from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.hooks.postgres_hook import PostgresHook
import datetime as dt
from shutil import copyfile
import time
import yaml
import os
import errno
import subprocess
from pathlib import Path
from slugify import slugify
import shutil
import json
import pprint

default_args = {
        'owner': 'me',
        'start_date': dt.datetime.utcnow() - dt.timedelta(days=22),
        'retries': 2,
        'retry_delay': dt.timedelta(minutes=5),
}

def create_with_parents(path_str):
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)

def create_dir_if_not_exists(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def resample(channels, input_file_name, output_prefix):
    for channel in channels:
        output_file_name = output_prefix + '-' + str(channel) + '.wav'
        create_with_parents(output_file_name)
        resample_command = ["sox", input_file_name, "-r16k", "-b16",
        output_file_name, "remix", str(channel)]
        result = subprocess.run(resample_command)

def move_input_task(**kwargs):
    metadata = kwargs['dag_run'].conf.get('metadata')
#    for attr in dir(obj):
#        print("obj.%s = %r" % (attr, getattr(obj, attr)))
    current_dir = os.getcwd()
    target_dir = current_dir + '/moved_input/' + kwargs['dag']._dag_id
    create_dir_if_not_exists(target_dir)
 
    for session in metadata['session']:
        for idx, mic in enumerate(session):
            # copy to json_id/raw/
            file_path = (session[idx]['filename'])
            file_name = os.path.basename(file_path)
#           print(file_name)
            src = current_dir + '/' + file_path
            dst = target_dir + '/' + file_name
            shutil.copyfile(src, dst)

def resample_task(**kwargs):
    params = kwargs['params']
    i = params['i']
    file_metadata = params['metadata']

    print(file_metadata)
    input_file_name = file_metadata['filename']
    channels = file_metadata['channels']
    file_dir = 'output/pipeline_%d/session_%d/%s' % (params['metadata_id'],
            params['session_num'], 
            file_metadata['type'])
    output_dir = file_dir + '/0_raw'
    create_dir_if_not_exists(output_dir)
    basename = os.path.splitext(os.path.basename(input_file_name))[0]
    output_prefix = output_dir + '/' + basename 
    resample(channels, input_file_name, output_prefix)

    return output_dir, basename, file_dir

def segmentation_task(**kwargs):
    ti = kwargs['ti']
    i = kwargs['params']['i']
    msg = ti.xcom_pull(task_ids='resample_ceiling_%d' % i)
    resample_dir = os.getcwd() + '/' + msg[0]
    resample_file_id = msg[1] 
    output_dir = os.getcwd() + '/' + msg[2] + '/1_clean'
    create_dir_if_not_exists(output_dir)
    vad_dir = '/home/shubham/backend_asr/vad8_dnn'
    vad_script = 'vad_DNN_v4_test2.sh'
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    intm_id = '%s%d' % (kwargs['ts_nodash'], i)
    vad_command = ["bash", vad_script, resample_dir, output_dir, intm_id]
    
    print("vad command")
    print(subprocess.list2cmdline(vad_command))
    print("intm_id")
    print(intm_id)
    print("resample_file_id")
    print(resample_file_id)
    print("resample_dir")
    print(resample_dir)
    print("output_dir")
    print(output_dir)
    subprocess.run(vad_command, env=my_env, cwd=vad_dir)


def process_records():
    # We will keep the records of the last 2 days. As soon as the dag becomes
    # older than 2 days, its dag will not be returned and the pipeline cannot
    # be seen again.
    days_threshold = 30
    date_threshold = (dt.date.today() - dt.timedelta(days_threshold)).isoformat()
    select_sql = "SELECT id, filename from metadata_registry where created_at > \
    '{}'".format(date_threshold)

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
    with open(metadata_file_path, "r") as stream:
        try:
            metadata = json.loads(stream.read())
        except ValueError as exc:
            print(exc)
    
    return metadata

dag1 = DAG('db_record_processing_v04',
          default_args=default_args,
          schedule_interval = '*/1 * * * *')

op = DummyOperator(task_id='dummy', dag=dag1)
t_process_records = PythonOperator(task_id='process_records',
                                   python_callable=process_records,
                                   dag=dag1)

metadata_record_list = process_records()

for metadata_id, file_path in metadata_record_list:
    metadata = parse_metadata(file_path)
    
    for idx, session in enumerate(metadata['session']):
        dag2_id = 'db_pipeline_v12_%s_session_%d' % (metadata_id, idx + 1) 
        dag2 = DAG(dag2_id,
                   default_args=default_args,
                   schedule_interval='@once')

        for i in range(1, len(session) + 1):
            t_resample_ceiling = PythonOperator(task_id='resample_ceiling_%d' % i,
                                                python_callable=resample_task,
                                                params={
                                                    "i": i,
                                                    "metadata_id": metadata_id,
                                                    "session_num": idx + 1,
                                                    "metadata":metadata['session'][idx][i-1]
                                                },
                                                dag=dag2,
                                                provide_context=True)

            t_segmentation = PythonOperator(task_id='segmentation_%d' % i,
                                            params={
                                                "i": i,
                                            },
                                            dag=dag2,
                                            python_callable=segmentation_task,
                                            provide_context=True)
            

            t_resample_ceiling >> t_segmentation

        globals()[dag2_id] = dag2

