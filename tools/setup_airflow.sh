sed -i -e "s@CURRENT_DIR@$(pwd)@g" airflow.cfg

eval "$(pyenv init -)"
pyenv activate asr_airflow
AIRFLOW__CORE__SQL_ALCHEMY_CONN="postgresql+psycopg2://127.0.0.1:5432/asr_airflow?user=asr_airflow&password=asr_airflow_password"
AIRFLOW_CONN_AIRFLOW_DB="postgresql://airflow@127.0.0.1:5432/airflow"
airflow initdb