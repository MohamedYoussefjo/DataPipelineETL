# DataPipelineETL By Mohamed Youssef Jouini and Youssef Alouane 
!!!!!!!!!! Still the security phase is not implemented properly ( ssl/TLS , authentication , authorization )  ((Version 1.0) next version + Security enhanced
This is our data pipeline for Orange Tunisia
## First things First :
we need to create .env file where the docker-compose file is located 
so we execute these commands over here :
echo "HOST_IP=$(hostname -I | awk '{print $1}')" > .env
echo "postgresuser=airflow" >> .env
echo "postgrespassword=youssef" >> .env
echo "postgresdbname=airflow" >> .env
echo "redispassword=youssef" >> .env
echo "webserverseckey=youssef" >> .env
echo "fernetkey=FIEQwFNkIf20aJVQ3seBdK4_vDX7qaGT9xy9MvGDNKY=" >> .env
## After that : 
we go to the directory after pulling it from my repository 
then we do : (we assume that  docker-compose is installed by : sudo apt-get install docker-compose )
### sudo su 
### docker-compose up -d 
### chmod -R 777 ./
U can just execute the script setup.sh as administrator (SUDO) to all that bet we need to change the environment variables with strong passwords 
## Now we need to configure the connection between the webserve http://localhost:8080
we go to connections tab and we specify host : spark://ipaddressofthemachine!!!!!! if we put localhost it resolves to the webserver ip 
and we specify the port to 7077 
## We Have 3 dags 
### 1 dag :  run every 1 minute same as the time of generation of data (xml files only)
### 2 dag :  run every 15 minute (Gzip to xml extraction )
### 3 dag :  run every 30 minute  (Csv files )
# OUR fOLDERS Tree : 
── gzip/
│   ├── gzipinput/       # Input of our data
│   ├── gzipcomplet/
│   ├── gzipbackup/
│   ├── jsoncoming/
│   ├── jsondone/
│   ├── jsonbackup/
│   ├── xmlbackup/
│   ├── xmlcoming/
│   └── xmldone/
├──xmlonly/
│   ├── xmlin/           # Input of our data
│   ├── xmldone/
│   ├── xmlbackup/
│   ├── jsonout/
│   ├── jsondone/
│   └── jsonbackup/
├── dags/                # Airflow DAGs
│   ├──dag.py
│   ├── mydag.py
│   ├── 1ercsvprocess.py
├── mypy/
│   ├── xmlonly.py  # Scripts executed by DAGs
│   ├── streaming.py
│   ├── preprocessproduce.py
├── csv/
│   ├── inputcsv/        # Input of our data
│   ├── jobdone/
│   └── backups/

# THE Topics  
We have 3 topics : 
-xmlt_fast for the first dag only for xml files 
-xmlt for the second dag gzip files 
-csv for the csv files with a specific header 
If not created we create them from kafdrop http://localhost:8900 
