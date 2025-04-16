# DataPipelineETL By Mohamed Youssef Jouini and Youssef Alouane 
!!!!!!!!!! Still the security phase is not implemented properly ( ssl/TLS , authentication , authorization )  ((Version 1.0) next version + Security enhanced
This is our data pipeline for Orange Tunisia


## First things First :
Execute the script setup.sh as administrator 
but we need to change the passwords to strong ones and generate another fernet key in the setup.sh 


## Our UI intefaces :

localhost:9090 spark UI 

localhost:8900 kafdrop 

localhost:8080 airflow webserver

localhost:5601 Kibana


## We Have 3 dags 
### 1 dag :  run every 1 minute same as the time of generation of data (xml files only)
### 2 dag :  run every 15 minute (Gzip to xml extraction )
### 3 dag :  run every trigger (trigger when there is a csv file to process )  (Csv files )



# Our folders Tree :
── gzip/

│   ├── gzipinput/   

│   ├── gzipcomplet/

│   ├── gzipbackup/

│   ├── jsoncoming/

│   ├── jsondone/

│   ├── jsonbackup/

│   ├── xmlbackup/

│   ├── xmlcoming/

│   └── xmldone/

├──xmlonly/

│   ├── xmlin/ 

│   ├── xmldone/

│   ├── xmlbackup/

│   ├── jsonout/

│   ├── jsondone/

│   └── jsonbackup/

├── dags/        

│   ├──dag.py

│   ├── mydag.py  (  in every dag here we need to specify the configuration of our spark-submit according to our infrastructure we find it in the spark-job section down  )

│   ├── 1ercsvprocess.py

├── mypy/

│   ├── xmlonly.py  

│   ├── streaming.py      

│   ├── preprocessproduce.py

├── csv/

│   ├── inputcsv/       

│   ├── jobdone/

│   └── backups/



# The Topics  
We have 3 topics : 

-xmlt_fast for the first dag only for xml files 

-xmlt for the second dag gzip files 

-csv for the csv files with a specific header 

If not created we create them from kafdrop http://localhost:8900 

# Finally 

just we put our files in the input directory 


# Visualisation 

we go to h http://localhost:5601 and we go stack management and we create index patterns then we create our dashboard there 
