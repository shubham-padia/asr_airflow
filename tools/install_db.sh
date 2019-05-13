psql -c "CREATE USER asr_airflow WITH PASSWORD 'asr_airflow_password';"
psql -c "CREATE DATABASE asr_airflow WITH OWNER asr_airflow;"
psql -c "CREATE USER watcher WITH PASSWORD 'yeshallnotpass';"
psql -c "CREATE DATABASE watcher WITH OWNER watcher;"