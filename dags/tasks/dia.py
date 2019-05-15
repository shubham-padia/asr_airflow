import os
import subprocess

from tasks.helpers import create_dir_if_not_exists
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable

from envparse import env

def dia_task(**kwargs):
    ti = kwargs['ti']
    params = kwargs['params']
    session_num = params['session_num']
    mic_name = params['mic_name']
    speaker_id = params['speaker_id']
    parent_data = ti.xcom_pull(task_ids='resample_%s' % mic_name)

    resample_dir = parent_data['output_dir']
    file_id = parent_data['file_id']
    resample_name = "%s-session%s-%s-%s" % (file_id, session_num, mic_name,
            speaker_id)
    resample_file = resample_dir + '/' + resample_name + '.wav'
    
    output_dir = parent_data['file_dir'] + '/1_clean_dia'
    output_file = output_dir + '/' + resample_name + '.seg'
    create_dir_if_not_exists(output_dir)

    env.read_envfile()
    lium_path = env('LIUM_PATH')

    dia_command = ['java', '-Xmx2048m', '-jar', lium_path, '--fInputMask=' +
                   resample_file, '--sOutputMask=' + output_file, '--doCEClustering', resample_name]
    
    subprocess.check_call(dia_command)

    return {
        'task_type': 'dia',
        'output_dir': output_dir,
        'file_id': file_id
    }

def get_dia_task(session_num, mic_name, file_id, speaker_id, dag):
    t_dia = PythonOperator(task_id='diarization_%s_%s' %
        (mic_name, speaker_id),
        params={
            "mic_name": mic_name,
            "file_id": file_id,
            "speaker_id": speaker_id,
            "session_num": session_num
        },
        dag=dag,
        python_callable=dia_task,
        provide_context=True)

    return t_dia
