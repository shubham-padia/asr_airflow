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
    basename = '181204_142512-m'
    output_prefix = output_dir + '/' + basename 
    resample(channels, input_file_name, output_prefix)

    return output_dir, basename

def segmentation_task(**kwargs):
    ti = kwargs['ti']
    msg = ti.xcom_pull(task_ids='resample_ceiling')
    resample_dir = os.getcwd() + '/' + msg[0]
    resample_file_id = msg[1]
    output_dir = os.getcwd() + '/1_clean/'
    create_with_parents(output_dir)
    vad_dir = '/home/shubham/backend_asr/vad8_dnn'
    vad_script = 'vad_DNN_v4_test2.sh'
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    vad_command = ["bash", vad_script, resample_dir, output_dir, resample_file_id]
    subprocess.run(vad_command, env=my_env, cwd=vad_dir)

with DAG('test_asr_v01',
        default_args=default_args,
        schedule_interval=None,
        ) as dag:

    t_resample_ceiling = PythonOperator(task_id='resample_ceiling',
                                        python_callable=resample_task,
                                        provide_context=True)

    t_segmentation = PythonOperator(task_id='segmentation',
                                    python_callable=segmentation_task,
                                    provide_context=True)


t_resample_ceiling >> t_segmentation
