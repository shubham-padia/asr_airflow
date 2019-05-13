cp example-nginx-config nginx-config
IP_ARRAY=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
IP=$(echo $IP_ARRAY | awk -F\  '{print $NF}')
sed -i -e "s/server_domain_or_IP/$IP/g" nginx-config
sudo cp nginx-config /etc/nginx/sites-available/asr_airflow
sudo ln -s /etc/nginx/sites-available/asr_airflow /etc/nginx/sites-enabled