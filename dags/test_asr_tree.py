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

from tasks.resample import get_resample_task
from tasks.helpers import change_segment_id, create_dir_if_not_exists

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

def vad_task(**kwargs):
    ti = kwargs['ti']
    msg = ti.xcom_pull(task_ids='resample_%s' % kwargs['params']['mic_name'])
    
    resample_dir = os.getcwd() + '/' + msg[0]
    resample_file_id = msg[1] 
    output_dir = os.getcwd() + '/' + msg[2] + '/1_clean'
    create_dir_if_not_exists(output_dir)
    
    vad_dir = '/home/shubham/backend_asr/vad8_dnn'
    vad_script = 'vad_DNN_v4_test2.sh'
    
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    intm_id = kwargs['ts_nodash'] + str(kwargs['params']['session_num']) + \
    kwargs['params']['mic_name'] 
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
    subprocess.check_call(vad_command, env=my_env, cwd=vad_dir)

    return output_dir, msg[1], resample_file_id

def get_vad_task(mic_name, session_name, pipeline_name, dag):
    t_vad = PythonOperator(task_id='vad_%s' %
        mic_name,
        params={
            "mic_name": mic_name,
            "session_num": session_num,
            "pipeline_name": pipeline_name
        },
        dag=dag,
        python_callable=vad_task,
        provide_context=True)

    return t_vad

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
            dag=dag2,
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

