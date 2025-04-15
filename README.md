# DataPipelineETL By Mohamed Youssef Jouini and Youssef Alouane 
!!!!!!!!!! Still the security phase is not implemented properly ( ssl/TLS , authentication , authorization )  ((Version 1.0) next version + Security enhanced
This is our data pipeline for Orange Tunisia
## First things First :
Execute the script setup.sh as administrator 
but we need to change the passwords to strong ones and generate another fernet key is the setup.sh 



## Now we need to configure the connection between the webserver  http://localhost:8080 and spark master
we go to connections tab and we specify host : spark://ipaddressofthemachine!!!!!! if we put localhost it resolves to the webserver ip 
and we specify the port to 7077 
## We Have 3 dags 
### 1 dag :  run every 1 minute same as the time of generation of data (xml files only)
### 2 dag :  run every 15 minute (Gzip to xml extraction )
### 3 dag :  run every 30 minute  (Csv files )



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

│   ├── mydag.py

│   ├── 1ercsvprocess.py

├── mypy/

│   ├── xmlonly.py  

│   ├── streaming.py

│   ├── preprocessproduce.py

├── csv/

│   ├── inputcsv/       

│   ├── jobdone/

│   └── backups/



# THE Topics  
We have 3 topics : 

-xmlt_fast for the first dag only for xml files 

-xmlt for the second dag gzip files 

-csv for the csv files with a specific header 

If not created we create them from kafdrop http://localhost:8900 

# Finally 

jut we put our files in the input directory 
