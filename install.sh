sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev libffi-dev liblzma-dev python-openssl git

curl https://pyenv.run | bash
pyenv install 3.7.2
pyenv virtualenv 3.7.2 asr_airflow
pyenv activate asr_airflow
export SLUGIFY_USES_TEXT_UNIDECODE=yes
pip install -r requirements.txt

sudo apt-get install postgresql postgresql-contrib libssl-dev
cp env-example .env
sed -i -e "s/padia/$USER/g" .env

cd app
python manage.py migrate

