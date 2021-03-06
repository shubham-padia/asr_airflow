from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor
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
        for mic_id in session:
            # copy to json_id/raw/
            file_path = (session[mic_id]['filename'])
            file_name = os.path.basename(file_path)
 #           print(file_name)
            src = current_dir + '/' + file_path
            dst = target_dir + '/' + file_name
            shutil.copyfile(src, dst)

def resample_task(**kwargs):
    metadata = kwargs['dag_run'].conf.get('metadata')
    file_metadata = metadata['session'][0]['ceiling']
    input_file_name = file_metadata['filename']
    channels = file_metadata['channels']
    output_dir = '0_raw'
    basename = os.path.splitext(os.path.basename(input_file_name))[0]
    output_prefix = output_dir + '/' + basename 
    resample(channels, input_file_name, output_prefix)

    return output_dir, basename

def segmentation_task(**kwargs):
    ti = kwargs['ti']
    msg = ti.xcom_pull(task_ids='resample_ceiling')
    resample_dir = os.getcwd() + '/' + msg[0]
    resample_file_id = msg[1] 
    output_dir = os.getcwd() + '/1_clean'
    create_with_parents(output_dir)
    vad_dir = '/home/shubham/backend_asr/vad8_dnn'
    vad_script = 'vad_DNN_v4_test2.sh'
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    vad_command = ["bash", vad_script,
            '/home/shubham/github/asr_airflow/0_raw',
            '/home/shubham/github/asr_airflow/1_clean',
            resample_file_id]
    
    print("resample_file_id")
    print(resample_file_id)
    print("resample_dir")
    print(resample_dir)
    print("output_dir")
    print(output_dir)
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
    
    t_move_input = PythonOperator(task_id='move_input',
                                  python_callable=move_input_task,
                                  provide_context=True)

t_resample_ceiling >> t_segmentation
