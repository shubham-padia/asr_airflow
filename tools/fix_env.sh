cp env-example .env
sed -i -e "s/shubham/$USER/g" .env
sed -i -e "s@CURRENT_DIR@$(pwd)@g" .env
IP_ARRAY=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
IP=$(echo $IP_ARRAY | awk -F\  '{print $NF}')
sed -i -e "s/server_domain_or_IP/$IP/g" .env