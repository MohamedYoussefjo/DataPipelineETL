# DataPipelineETL - Orange Tunisia

**Authors**: Mohamed Youssef Jouini, Youssef Alouane  
**Version**: 1.0  
⚠️ **Security Notice**: SSL/TLS, authentication, and authorization not yet implemented (Planned for next version)

## Initial Setup

### 1. Launch the Pipeline

Execute setup.sh as administrator (use stronger passwords for production change the passwords in the setup.sh)

--Airflow Configuration

--Access the webserver at: http://localhost:8080

--Spark Connection Setup

--Go to Connections tab

--Set host to: spark://[YOUR_MACHINE_IP] (never use localhost)

--Set port to: 7077

## DAGs Schedule

DAG Name	Frequency	Description

XML Processor	Every 1 minute	Processes XML files

Gzip Extractor	Every 15 minutes	Extracts XML from Gzip files

CSV Processor	Every 30 minutes	Processes CSV files


## Directory Structure

├── Gzip/

│   ├── gzipinput/

│   ├── gzipcomplet/

│   ├── gzipbackup/

│   ├── jsoncoming/

│   ├── jsondone/

│   ├── jsonbackup/

│   ├── xmlbackup/

│   ├── xmlcoming/

│   └── xmldone/

├── xmlonly/

│   ├── xmlin/ 

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

│   ├── inputcsv/ 

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
