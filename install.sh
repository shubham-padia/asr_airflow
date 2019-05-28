bash tools/install_dependencies.sh
bash tools/install_pyenv.sh
bash tools/install_python_deps.sh
bash tools/fix_env.sh
bash tools/setup_services.sh
sudo su -c "bash $(pwd)/tools/install_db.sh" - postgres
bash tools/setup_airflow.sh
bash tools/setup_app.sh
