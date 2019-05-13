cp example_services/* services
sed -i -e "s/shubham/$USER/g" services/airflow-webserver.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/airflow-webserver.service
sed -i -e "s/shubham/$USER/g" services/airflow-scheduler.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/airflow-scheduler.service
sed -i -e "s/shubham/$USER/g" services/gunicorn.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/gunicorn.service
sudo cp services/* /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl enable airflow-webserver
sudo systemctl enable airflow-scheduler