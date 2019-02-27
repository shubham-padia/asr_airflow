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
from helpers import change_segment_id

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
    pprint.pprint(kwargs)
    params = kwargs['params']
    session_metadata = params['session_metadata']
    parent_output_dir = params['parent_output_dir']

#    for attr in dir(obj):
#        print("obj.%s = %r" % (attr, getattr(obj, attr)))

    current_dir = os.getcwd()
    target_dir = "%s/moved_input/%s" % (current_dir, parent_output_dir)
            
    create_dir_if_not_exists(target_dir)
 
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
    mic_name = file_metadata['name']
    session_num = params['session_num']
    pipeline_name = params['pipeline_name']

    print(file_metadata)
    input_file_name = file_metadata['filename']
    channels = file_metadata['channels']
    file_dir = '%s/session%d/%s' % (params['parent_output_dir'],
            session_num,
            file_metadata['type'])
    output_dir = file_dir + '/0_raw'
    create_dir_if_not_exists(output_dir)
    
    output_prefix = '%s/%s-session%d-%s' %(output_dir, pipeline_name, session_num,
            mic_name) 
    resample(channels, input_file_name, output_prefix)

    return output_dir, pipeline_name,file_dir

def segmentation_task(**kwargs):
    ti = kwargs['ti']
    i = kwargs['params']['i']
    msg = ti.xcom_pull(task_ids='resample_%s' % kwargs['params']['mic_name'])
    
    resample_dir = os.getcwd() + '/' + msg[0]
    resample_file_id = msg[1] 
    output_dir = os.getcwd() + '/' + msg[2] + '/1_clean'
    create_dir_if_not_exists(output_dir)
    
    vad_dir = '/home/shubham/backend_asr/vad8_dnn'
    vad_script = 'vad_DNN_v4_test2.sh'
    
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    intm_id = kwargs['ts_nodash'] + str(kwargs['params']['session_num']) + str(i)
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

def decoder_task(**kwargs):
    params = kwargs['params']
    seg = params['seg']
    wav = params['wav']

    ti = kwargs['ti']
    seg_data = ti.xcom_pull(task_ids=seg['task_id'])
    wav_data = ti.xcom_pull(task_ids=wav['task_id'])
    
    output_prefix = "session%s-%s-seg-%s-wav-%s" % (params['session_num'],
            seg['channel'], seg['mic_name'], wav['mic_name'])
    output_dir = "%s/%s/session%d/hybrid/decoder/%s" % (os.getcwd(),
            params['parent_output_dir'], params['session_num'], output_prefix) 
    create_dir_if_not_exists(output_dir)
    
    
    # The decode bash script requires the segment file name and the wav
    # file name to be the same. We are using symlinks to make them have the
    # same file name. They also need to be in the same directory.
    seg_file = "%s/%s-session%s-%s-%s.seg" % (seg_data[0], seg_data[2],
            params['session_num'], seg['mic_name'], seg['channel'])
    wav_file = "%s/%s-session%s-%s-%s.wav" % (wav_data[0],
            wav_data[2], params['session_num'], wav['mic_name'], wav['channel'])
    
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
    metadata = parse_metadata(file_path)
    pipeline_name = os.path.splitext(os.path.basename(file_path))[0]
    parent_output_dir = "output/%s/%s" % (pipeline_name, created_at_str)

    if True:
        for idx, session in enumerate(metadata['session']):
            dag2_id = 'hybrid_%s_session_%d' % (pipeline_name, idx + 1) 
            dag2 = DAG(dag2_id,
                       default_args=default_args,
                       schedule_interval='@once')

            t_move_input_task = PythonOperator(task_id='move_input',
                                               dag=dag2,
                                               python_callable=move_input_task,
                                               params={
                                                   "parent_output_dir":
                                                   parent_output_dir,
                                                   "session_metadata":
                                                   metadata['session'][idx]
                                               },
                                               provide_context=True)
            
            for i in range(1, len(session) + 1):
                mic_metadata = metadata['session'][idx][i-1]

                t_resample_ceiling = PythonOperator(task_id='resample_%s' % mic_metadata['name'], 
                                                    python_callable=resample_task,
                                                    params={
                                                        "i": i,
                                                        "metadata_id": metadata_id,
                                                        "session_num": idx + 1,
                                                        "metadata": mic_metadata,
                                                        "parent_output_dir":
                                                        parent_output_dir,
                                                        "pipeline_name":
                                                        pipeline_name
                                                    },
                                                    dag=dag2,
                                                    provide_context=True)

                t_segmentation = PythonOperator(task_id='segmentation_%s' %

                    mic_metadata['name'],
                                                params={
                                                    "i": i,
                                                    "mic_name":
                                                    mic_metadata['name'],
                                                    "session_num": idx + 1,
                                                    "pipeline_name": pipeline_name
                                                },
                                                dag=dag2,
                                                python_callable=segmentation_task,
                                                provide_context=True)
                

                t_resample_ceiling >> t_segmentation
            print(metadata['hybrids'])
            session_hybrids = metadata['hybrids'].get(str(idx + 1), None)
            print("session hybrids: %s" % session_hybrids)            
            if session_hybrids:
                for hybrid in session_hybrids:
                    seg_hybrid = hybrid['seg']
                    seg_mic_name = seg_hybrid['mic_name']
                    seg_task_id = 'segmentation_%s' % seg_mic_name
                    seg_task = get_task_by_id(seg_task_id, dag2)
                    
                    wav_hybrid = hybrid['wav']
                    wav_mic_name = wav_hybrid['mic_name']
                    wav_task_id = 'segmentation_%s' % wav_mic_name
                    wav_task = get_task_by_id(wav_task_id, dag2)

                    t_decoder = PythonOperator(task_id='hybrid_seg_%s_wav_%s' % 
                            (seg_mic_name, wav_mic_name),
                            dag=dag2,
                            params={
                                "session_num": idx + 1,
                                "parent_output_dir": parent_output_dir,
                                "seg": {
                                    "task_id": seg_task_id,
                                    "channel": seg_hybrid['channel'],
                                    "mic_name": seg_mic_name
                                },
                                "wav": {
                                    "task_id": wav_task_id,
                                    "channel": wav_hybrid['channel'],
                                    "mic_name": wav_mic_name
                                }
                            },
                            python_callable=decoder_task,
                            provide_context=True
                            )

                    t_decoder.set_upstream(seg_task)
                    t_decoder.set_upstream(wav_task)

            globals()[dag2_id] = dag2

