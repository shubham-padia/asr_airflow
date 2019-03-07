# Dynamic Airflow Pipeline Generator

### Installation:
0.) Clone the repo:
```
git clone https://github.com/shubham-padia/asr_airflow
cd asr_airflow
```

1.) Install [pyenv](https://github.com/pyenv/pyenv) for managing virtual environments using [pyenv-installer](https://github.com/pyenv/pyenv-installer) (You can use any environment manager you like):
```bash
curl https://pyenv.run | bash
```

2.) Install Python 3.7.2
```
pyenv install 3.7.2
```

3.) Create virtual environment.
```
pyenv virtualenv 3.7.2 asr_airflow
```

4.) Activate virtual environment.
```
pyenv activate asr_airflow
```

5.) Install dependencies
```
pip install -r requirements.txt
```

6.) Postgres:
- Make sure postgres is installed:
```
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib libssl-dev
```
- Create the database. For that we first open the psql shell. Go the directory where your postgres file is stored.

```sh
# For linux users
sudo -u postgres psql

# For macOS users
psql -d postgres
```

* When inside psql, create a user for open-event and then using the user create the database. Also, create a test databse named opev_test for the test suites by dumping the oevent database into it. without this, the tests will not run locally.

```sql
CREATE USER asr_airflow WITH PASSWORD 'asr_airflow_password';
CREATE DATABASE asr_airflow WITH OWNER asr_airflow;
CREATE USER watcher WITH PASSWORD 'yeshallnotpass';
CREATE DATABASE watcher WITH OWNER watcher;
```

* Once the databases are created, exit the psql shell with `\q` followed by ENTER.

7.) Create the tables.
```
python models/create_db.py
alembic upgrade
```

8.) Create application environment variables.
```
cp env-example .env
```
- Change `AIRFLOW_HOME` to your current directory i.e. the one you cloned the project into.
- Change `AIRFLOW__CORE__SQL_ALCHEMY_CONN` and `AIRFLOW_CONN_AIRFLOW_DB` to point to the database we created earlier.
- Change `PATH` to your current path, make sure the virtual environment that we created earlier is active. You can view your current path by typing `echo $PATH`

9.) Change the systemd service paths and copy the systemd services to your system's service folder:
```
cp -r services/ /lib/systemd/system
systemctl enable watcher-to-db
systemctl enable airflow-scheduler
systemctl enable airflow-webserver
```

10.) Start the server
```
systemctl start watcher-to-db
systemctl start airflow-webserver
systemctl start airflow-scheduler
```