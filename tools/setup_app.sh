cd app
eval "$(pyenv init -)"
pyenv activate asr_airflow
python manage.py migrate

sudo ufw allow 8000
sudo ufw allow 7000
sudo ufw allow 2000
sudo ufw allow 'Nginx Full'
