# Dynamic Airflow Pipeline Generator

## Installation:
1.)
```
git clone https://github.com/shubham-padia/asr_airflow
cd asr_airflow
```
2.) run `bash install.sh`

3.) To deploy i.e run your project, execute `bash tools/deploy.sh`

## Changing the IP:
By default the installation script will pickup your network IP (which you can find by ifconfig) and use that.
If you want to change that IP to either 127.0.0.1 or some other IP please follow the below given instructions.

1.) Run `bash tools/change_ip.sh <your_ip_here >`

### Manual Installation:
0.) Clone the repo:
```
git clone https://github.com/shubham-padia/asr_airflow
cd asr_airflow
```

1.) Install [pyenv](https://github.com/pyenv/pyenv) for managing virtual environments using [pyenv-installer](https://github.com/pyenv/pyenv-installer) (You can use any environment manager you like):

Install prerequisites for Ubuntu/Debian:
```
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
```
For other distributions or any other build problems, please refer to the this [wiki](https://github.com/pyenv/pyenv/wiki/Common-build-problems)
 
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
export SLUGIFY_USES_TEXT_UNIDECODE=yes
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

7.) Create application environment variables.
```
cp env-example .env
```
- Change `AIRFLOW_HOME` to your current directory i.e. the one you cloned the project into.
- Change `AIRFLOW__CORE__SQL_ALCHEMY_CONN` and `AIRFLOW_CONN_AIRFLOW_DB` to point to the database we created earlier i.e. `asr_airflow` db.
- Change `PATH` to your current system path, make sure the virtual environment that we created earlier is active. You can view your current path by typing `echo $PATH`
- Set `WATCHER_DB_URL` to the url of the watcher database we created in the earlier steps.

8.) Create the tables and run migration.
```
cd app
python manage.py migrate
```

9.) Copy the example services from `example_services` to a directory named `services`.
Please try to name the directory for the actual services as `services` as it has been added
to the `.gitignore`.
```cp -r example_services/ services```

10.) Change the systemd service paths in the `services` directory according to your system:
- `EnvironmentFile` should point to the absolute location of the .env file
that we created in the earlier step.
- `User` should be your linux user name and `Group` should be your user group.
- `ExecStart` should use the binary present in your virtual environment.
e.g. `/home/user/.pyenv/versions/3.7.2/envs/asr_airflow/bin/airflow`
or `/home/user/.pyenv/versions/3.7.2/envs/asr_airflow/bin/python` for the python binary.
- In case of airflow webserver or scheduler, an extra argument for `--pid` is required in `ExecStart`
e.g. `--pid /home/user/github/asr_airflow/scheduler.pid`
- Set `WorkingDirectory` to `/home/user/github/asr_airflow`

11.) copy the systemd services to your system's service folder:

```
cp -r services/ /lib/systemd/system
systemctl enable watcher-to-db
systemctl enable airflow-scheduler
systemctl enable airflow-webserver
```

12.) Start the server
```
systemctl start watcher-to-db
systemctl start airflow-webserver
systemctl start airflow-scheduler
```

13.) 
- Go to Admin > Variables
- Import variables by choosing the file `airflow_default_variables.json`
- Change the variables to point to the path of scripts on your system.

##### Glossary:
- **Recording_id**: Usually the name of your Recording Info file i.e. the file that contains the information about the sessions, mic types and channels
- **Pipeline_id**: The name for the different combination of steps you are running for the same recording id. 
- **BASE_FOLDER**: The folder where asr_airflow has been installed.
- **Pipeline Creator**: The frontend for generating pipeline files.

##### Output file Structure:

- `BASE_FOLDER/<Recording_id>/<Pipeline_id>/<session(1/2/3...)>/<mic_name or "hybrid">/<0_raw or 1_vad or 1_dia or 2_decoder>/<Your_output_files>`

# Steps
1. Upload your audio files to `BASE_FOLDER/data/<Recording_id>`
2. Open the Pipeline Creator and upload you recording metadata files. Fill the name (which will be the name of the file you downlaod when you click the submit button), recording_id, version, and pipeline_id. **The combination of `Recording_id` + `Pipeline_id` should always be unique.** The name of the pipeline will be `<Recording_id>-<Pipeline_id>`.
3. Add steps for your pipeline in the steps section, check the graph for your steps by clicking `view graph` on the navbar. If you are satisfied with the graph, then click on the submit button and the file will be downloaded at <name>.json.
4. NOTE: To use the downloaded file for another recording metadata file, you can use the import function at the top of the navbar. The imported pipeline will the contain the old recording data. You can replace that by uploading the new metadata file. Please remember to first import the pipeline and then import the metadata file. 
5. Upload the downloaded metadata file to `BASE_FOLDER/metadata` directory. The file watcher in that directory will log the file in the database. The pipeline will then be registered to airflow after a wait of 1-2 mins.
6. Search for `<Recording_id>-<Pipeline_id>` in airflow and turn the toggle button in airflow for whichever session you want to run for the uploaded pipeline. Check the status of the pipeline to see whether the pipeline has been successfully executed.
