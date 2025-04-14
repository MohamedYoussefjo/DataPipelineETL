# DataPipelineETL - Orange Tunisia

**Authors**: Mohamed Youssef Jouini, Youssef Alouane  
**Version**: 1.0  
⚠️ **Security Notice**: SSL/TLS, authentication, and authorization not yet implemented (Planned for next version)

## Initial Setup

### 1. Environment Configuration
Create `.env` file in the same directory as `docker-compose.yml`:

```bash
echo "HOST_IP=$(hostname -I | awk '{print $1}')" > .env
echo "postgresuser=airflow" >> .env
echo "postgrespassword=youssef" >> .env
echo "postgresdbname=airflow" >> .env
echo "redispassword=youssef" >> .env
echo "webserverseckey=youssef" >> .env
echo "fernetkey=FIEQwFNkIf20aJVQ3seBdK4_vDX7qaGT9xy9MvGDNKY=" >> .env

2. Launch the Pipeline
bash
Copy
sudo su
docker-compose up -d
chmod -R 777 ./
Alternative: Execute setup.sh as administrator (use stronger passwords for production)

Airflow Configuration
Access the webserver at: http://localhost:8080

Spark Connection Setup:
Go to Connections tab

Set host to: spark://[YOUR_MACHINE_IP] (never use localhost)

Set port to: 7077

DAGs Schedule
DAG Name	Frequency	Description
XML Processor	Every 1 minute	Processes XML files
Gzip Extractor	Every 15 minutes	Extracts XML from Gzip files
CSV Processor	Every 30 minutes	Processes CSV files
Directory Structure
Copy
DataPipelineETL/
├── Gzip/
│   ├── gzipinput/    # Primary input directory
│   ├── gzipcomplet/
│   ├── gzipbackup/
│   ├── jsoncoming/
│   ├── jsondone/
│   ├── jsonbackup/
│   ├── xmlbackup/
│   ├── xmlcoming/
│   └── xmldone/
├── XMLonly/
│   ├── xmlin/        # Primary input directory
│   ├── xmldone/
│   ├── xmlbackup/
│   ├── jsonout/
│   ├── jsondone/
│   └── jsonbackup/
├── dags/
│   ├── csv_processor.py
│   ├── xml_processor.py
│   ├── gzip_processor.py
│   ├── preprocessing.py
│   └── kafka_sender.py
├── mypy/             # Custom scripts
├── csv/
│   ├── inputcsv/     # Primary input directory
│   ├── jobdone/
│   └── backups/
└── logs/
    ├── spark_connections/
    ├── spark_jobs/
    ├── stages/
    ├── warnings/
    └── errors/
