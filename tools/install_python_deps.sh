eval "$(pyenv init -)"
pyenv activate asr_airflow
export SLUGIFY_USES_TEXT_UNIDECODE=yes
pip install -r requirements.txt