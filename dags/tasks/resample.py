import subprocess
from ..helpers import create_dir_if_not_exists
from airflow.operators.python_operator import PythonOperator

def resample(channels, input_file_name, output_prefix):
    for idx, channel in enumerate(channels):
        output_file_name = output_prefix + '-' + str(idx + 1) + '.wav'
        resample_command = ["sox", input_file_name, "-r16k", "-b16",
        output_file_name, "remix", str(channel)]
        subprocess.run(resample_command)

def resample_task(**kwargs):
    params = kwargs['params']
    file_metadata = params['metadata']
    mic_name = params['mic_name']
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

def get_resample_task(mic_name, mic_metadata, session_num, dag,
        parent_output_dir, pipeline_name):

    return PythonOperator(
        task_id='resample_%s' % mic_name, 
        python_callable=resample_task,
        params={
            "session_num": session_num,
            "mic_name": mic_name,
            "metadata": mic_metadata,
            "parent_output_dir": parent_output_dir,
            "pipeline_name": pipeline_name
        },
        dag=dag,
        provide_context=True)