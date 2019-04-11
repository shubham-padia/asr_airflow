import os
from shutil import copyfile

from airflow.operators.python_operator import PythonOperator
from tasks.helpers import create_dir_if_not_exists

def move_input_task(**kwargs):
    params = kwargs['params']
    session_metadata = params['session_metadata']
    parent_output_dir = params['parent_output_dir']

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
        copyfile(src, dst)

def get_move_input_task(dag, parent_output_dir, session_metadata):
    return PythonOperator(
                task_id='move_input',
                dag=dag,
                python_callable=move_input_task,
                params={
                    "parent_output_dir": parent_output_dir,
                    "session_metadata": session_metadata
                },
                provide_context=True
            )