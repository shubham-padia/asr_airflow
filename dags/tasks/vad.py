import os
import subprocess
from tasks.helpers import create_dir_if_not_exists
from airflow.operators.python_operator import PythonOperator

def vad_task(**kwargs):
    ti = kwargs['ti']
    parent_data = ti.xcom_pull(task_ids='resample_%s' % kwargs['params']['mic_name'])
    
    resample_dir = os.getcwd() + '/' + parent_data['output_dir']
    resample_file_id = parent_data['file_id']
    output_dir = os.getcwd() + '/' + parent_data['file_dir'] + '/1_clean'
    create_dir_if_not_exists(output_dir)
    
    vad_dir = '/home/shubham/backend_asr/vad8_dnn'
    vad_script = 'vad_DNN_v4_test2.sh'
    
    my_env=os.environ.copy()
    my_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    intm_id = kwargs['ts_nodash'] + kwargs['params']['mic_name'] 
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

    return {
        'task_type': 'vad',
        'output_dir': output_dir,
        'file_id': parent_data['file_id']
    }

def get_vad_task(mic_name, session_name, file_id, dag):
    t_vad = PythonOperator(task_id='vad_%s' %
        mic_name,
        params={
            "mic_name": mic_name,
            "file_id": file_id
        },
        dag=dag,
        python_callable=vad_task,
        provide_context=True)

    return t_vad