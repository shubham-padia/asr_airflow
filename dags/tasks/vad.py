import os
import subprocess

from tasks.helpers import create_dir_if_not_exists
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable

def vad_task(**kwargs):
    ti = kwargs['ti']
    parent_data = ti.xcom_pull(task_ids='resample_%s' % kwargs['params']['mic_name'])
    
    resample_dir = parent_data['output_dir']
    output_dir = parent_data['file_dir'] + '/1_clean_vad'
    create_dir_if_not_exists(output_dir)
    
    vad_dir = Variable.get("vad_dir")
    vad_script = Variable.get("vad_script")
    
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    intm_id = kwargs['ts_nodash'] + 'session' + str(kwargs['params']['session_num']) + kwargs['params']['mic_name']
    vad_command = ["bash", vad_script, resample_dir, output_dir, intm_id]

    subprocess.check_call(vad_command, env=my_env, cwd=vad_dir)

    return {
        'task_type': 'vad',
        'output_dir': output_dir,
        'file_id': parent_data['file_id']
    }

def get_vad_task(session_num, mic_name, dag):
    t_vad = PythonOperator(task_id='vad_%s' %
        mic_name,
        params={
            "session_num": session_num,
            "mic_name": mic_name
        },
        dag=dag,
        python_callable=vad_task,
        provide_context=True)

    return t_vad
