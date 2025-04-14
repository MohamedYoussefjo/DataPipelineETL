DataPipelineETL
By Mohamed Youssef Jouini and Youssef Alouane
Version 1.0

Important Security Notice:
❗ This version lacks proper SSL/TLS, authentication, and authorization. Security enhancements planned for next release.

Initial Setup
1. Create .env File
Run these commands where docker-compose.yml is located:

Copy
echo "HOST_IP=$(hostname -I | awk '{print $1}')" > .env  
echo "postgresuser=airflow" >> .env  
echo "postgrespassword=youssef" >> .env  
echo "postgresdbname=airflow" >> .env  
echo "redispassword=youssef" >> .env  
echo "webserverseckey=youssef" >> .env  
echo "fernetkey=FIEQwFNkIf20aJVQ3seBdK4_vDX7qaGT9xy9MvGDNKY=" >> .env
2. Launch the Pipeline
After pulling the repository:

Copy
sudo su  
docker-compose up -d  
chmod -R 777 ./
Alternatively execute setup.sh as administrator

Airflow Configuration
Access webserver at: http://localhost:8080

Spark Connection Setup:

Go to Connections tab

Set host to: spark://[YOUR_MACHINE_IP] (not localhost)

Set port to: 7077

DAGs Schedule
DAG 1: Runs every 1 minute (XML files processing)

DAG 2: Runs every 15 minutes (Gzip to XML extraction)

DAG 3: Runs every 30 minutes (CSV files processing)

Folder Structure
Main Directories:
Gzip/

XMLonly/

dags/ (Airflow DAGs)

mypy/ (Execution scripts)

csv/

logs/

Subdirectories:
Gzip/

gzipinput/ (input data)

gzipcomplet/

gzipbackup/

jsoncoming/

jsondone/

jsonbackup/

xmlbackup/

xmlcoming/

xmldone/

XMLonly/

xmlin/ (input data)

xmldone/

xmlbackup/

jsonout/

jsondone/

jsonbackup/

dags/

csv_processor.py

xml_processor.py

gzip_processor.py

preprocessing.py

kafka_sender.py

csv/

inputcsv/ (input data)

jobdone/

backups/

logs/

spark_connections/

spark_jobs/

stages/

warnings/

errors/

Kafka Topics
Create these topics via Kafdrop (http://localhost:8900) if they don't exist:

xmlt_fast (for first DAG)

xmlt (for second DAG)

csv (for CSV files with specific header)

Security Warning
Current version uses default credentials for development only:

All passwords set to "youssef"

Hardcoded Fernet key

Production requires:

Strong password generation

SSL/TLS implementation

Proper authentication

Secure file permissions (avoid 777)

Next Version Plans:

Enhanced security implementation

Proper secret management

Production-ready configuration
