from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor
import datetime as dt
from shutil import copyfile
import time
import yaml
import os
import subprocess
from pathlib import Path
from slugify import slugify

default_args = {
        'owner': 'me',
        'start_date': dt.datetime.utcnow() - dt.timedelta(days=22),
        'retries': 2,
        'retry_delay': dt.timedelta(minutes=5),
}

def create_with_parents(path_str):
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)

def resample(channels, input_file_name, output_prefix):
    for channel in channels:
        output_file_name = output_prefix + '-' + str(channel) + '.wav'
        create_with_parents(output_file_name)
        resample_command = ["sox", input_file_name, "-r16k", "-b16",
        output_file_name, "remix", str(channel)]
        result = subprocess.run(resample_command)

def resample_task(**kwargs):
    metadata = kwargs['dag_run'].conf.get('metadata')
    print("==============================================")
    print(os.getcwd())
    print("==============================================")
    file_metadata = metadata['session'][0]['ceiling']
    input_file_name = file_metadata['filename']
    channels = file_metadata['channels']
    output_dir = '0_raw'
    output_prefix = output_dir + '/181204_142512-m' 
    resample(channels, input_file_name, output_prefix)

with DAG('test_asr_v01',
        default_args=default_args,
        schedule_interval=None,
        ) as dag:

    t_resample_ceiling = PythonOperator(task_id='resample_ceiling',
                                        python_callable=resample_task,
                                        provide_context=True)


