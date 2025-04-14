# DataPipelineETL - Orange Tunisia

**Authors**: Mohamed Youssef Jouini, Youssef Alouane  
**Version**: 1.0  
⚠️ **Security Notice**: SSL/TLS, authentication, and authorization not yet implemented (Planned for next version)

## Initial Setup

### 1. Environment Configuration

Create `.env` file in the same directory as `docker-compose.yml`:
echo "HOST_IP=$(hostname -I | awk '{print $1}')" > .env
echo "postgresuser=airflow" >> .env
echo "postgrespassword=youssef" >> .env
echo "postgresdbname=airflow" >> .env
echo "redispassword=youssef" >> .env
echo "webserverseckey=youssef" >> .env
echo "fernetkey=FIEQwFNkIf20aJVQ3seBdK4_vDX7qaGT9xy9MvGDNKY=" >> .env

### 2. Launch the Pipeline

sudo su
docker-compose up -d
chmod -R 777 ./
Alternative: Execute setup.sh as administrator (use stronger passwords for production)
Airflow Configuration
Access the webserver at: http://localhost:8080
Spark Connection Setup
Go to Connections tab
Set host to: spark://[YOUR_MACHINE_IP] (never use localhost)
Set port to: 7077

## DAGs Schedule

DAG Name	Frequency	Description

XML Processor	Every 1 minute	Processes XML files

Gzip Extractor	Every 15 minutes	Extracts XML from Gzip files

CSV Processor	Every 30 minutes	Processes CSV files


##Directory Structure
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
├── xmlonly/
│   ├── xmlin/        # Primary input directory
│   ├── xmldone/
│   ├── xmlbackup/
│   ├── jsonout/
│   ├── jsondone/
│   └── jsonbackup/
├── dags/
│   ├── processproduce.py
│   ├── dag.py
│   ├──-mydag.py
│   
│ 
├── mypy/            
├── csv/
│   ├── inputcsv/     # Primary input directory
│   ├── jobdone/
│   └── backups/



Create these topics via Kafdrop (http://localhost:8900) if missing:

xmlt_fast : XML processing stream

xmlt : Gzip extraction pipeline

csv : CSV processing (requires specific header format)

Security Considerations
Current Development Setup (⚠️ Not for production):

Default password: "youssef" for all services

Hardcoded Fernet key

Permissions set to 777 (insecure)

Planned Security Upgrades:

End-to-end SSL/TLS encryption

Role-based authentication

Fine-grained authorization

Secrets management system

Secure permission model (755/644)
