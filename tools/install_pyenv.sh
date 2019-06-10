curl https://pyenv.run | bash
pyenv install 3.7.2
pyenv virtualenv 3.7.2 asr_airflow
echo "export PATH=\"${PYENV_ROOT}/bin:\$PATH\"" >> ~/.bashrc
echo "eval \"\$(pyenv init -)\""  >> ~/.bashrc
echo "eval \"\$(pyenv virtualenv-init -)\""  >> ~/.bashrc
source ~/.bashrc
