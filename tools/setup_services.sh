mkdir -p services
mkdir -p output
cp example_services/* services
sed -i -e "s/shubham/$USER/g" services/airflow-webserver.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/airflow-webserver.service
sed -i -e "s/shubham/$USER/g" services/airflow-scheduler.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/airflow-scheduler.service
sed -i -e "s/shubham/$USER/g" services/gunicorn.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/gunicorn.service
sed -i -e "s/shubham/$USER/g" services/file-listing-server.service
sed -i -e "s@CURRENT_DIR@$(pwd)@g" services/file-listing-server.service
IP_ARRAY=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
IP=$(echo $IP_ARRAY | awk -F\  '{print $NF}')
sed -i -e "s/server_domain_or_IP/$IP/g" services/gunicorn.service
sudo cp services/* /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl enable airflow-webserver
sudo systemctl enable airflow-scheduler
sudo systemctl enable file-listing-server