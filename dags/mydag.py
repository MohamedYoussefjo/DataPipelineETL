from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import BranchPythonOperator
import os
import xml.etree.ElementTree as ET
import json
import shutil
import gzip
from glob import glob
import time

default_args = {
    'owner': 'youssef',
    'depends_on_past': False,
    'start_date': datetime(2025, 4, 13),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'xml_to_kafka_pipeline',
    default_args=default_args,
    description='Process XML to JSON and stream to Kafka',
    schedule_interval='*/15 * * * *',
    catchup=False,
    max_active_runs=1
)

config = {
    # GZIP paths
    'gzip_input_dir': '/app/gzip/gzipinput',
    'gzip_complete_dir': '/app/gzip/gzcomplet',
    'gzip_backup_dir': '/app/gzip/gzipbackup',
    
    # XML paths
    'xml_input_dir': '/app/gzip/xmlcoming',
    'xml_processed_dir': '/app/gzip/xmldone',
    'xml_backup_dir': '/app/gzip/xmlbackup',
    
    # JSON paths
    'json_output_dir': '/app/gzip/jsoncoming',
    'json_processed_dir': '/app/gzip/jsondone',
    'json_backup_dir': '/app/gzip/jsonbackup',
    
    # Kafka config
    'kafka_bootstrap': '192.168.253.129:9092',
    'kafka_topic': 'xmlt',
    
    # XML namespace
    'namespace': {'ns': 'http://www.3gpp.org/ftp/specs/archive/32_series/32.435#measCollec'},
    
    # Retention
    'days_to_keep': 7
}

def ensure_directories_exist():
    """Ensure all required directories exist"""
    for dir_path in [
        config['gzip_input_dir'], config['gzip_complete_dir'], config['gzip_backup_dir'],
        config['xml_input_dir'], config['xml_processed_dir'], config['xml_backup_dir'],
        config['json_output_dir'], config['json_processed_dir'], config['json_backup_dir']
    ]:
        os.makedirs(dir_path, exist_ok=True)

def process_gzip_files(**kwargs):
    """Extract XML files from gzip archives"""
    ensure_directories_exist()
    processed_count = 0
    
    gz_files = glob(os.path.join(config['gzip_input_dir'], '*.gz'))
    
    if not gz_files:
        print("No GZIP files found to process")
        return 0

    for gz_path in gz_files:
        try:
            filename = os.path.basename(gz_path)
            
            # Handle .xml.gz files properly
            if filename.endswith('.xml.gz'):
                xml_filename = filename[:-3]  # Remove .gz
            else:
                xml_filename = filename.replace('.gz', '.xml')
            
            xml_path = os.path.join(config['xml_input_dir'], xml_filename)
            
            # Extract XML
            with gzip.open(gz_path, 'rb') as f_in:
                with open(xml_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Move processed gz
            completed_path = os.path.join(config['gzip_complete_dir'], filename)
            shutil.move(gz_path, completed_path)
            
            # Create timestamped backup
            backup_filename = os.path.basename(filename)  # Keep original name
            backup_path = os.path.join(config['gzip_backup_dir'], backup_filename)

	    # Handle duplicates by adding a counter
            counter = 1
            while os.path.exists(backup_path):
                base, ext = os.path.splitext(backup_filename)
                backup_path = os.path.join(config['gzip_backup_dir'], f"{base}_{counter}{ext}")
                counter += 1
            shutil.copy2(completed_path, backup_path)
            
            processed_count += 1
            print(f"Processed {filename} → {xml_filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue
    
    return processed_count

def process_xml_files(**kwargs):
    """Convert XML files to timestamped JSON"""
    ensure_directories_exist()
    processed_count = 0
    combined_data = []
    
    # Generate unique timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"combined_{timestamp}.json"
    combined_json_path = os.path.join(config['json_output_dir'], combined_filename)
    xml_files = glob(os.path.join(config['xml_input_dir'], '*.xml'))
    
    if not xml_files:
        print("No XML files found to process")
        return 0

    for xml_path in xml_files:
        try:
            filename = os.path.basename(xml_path)
            
            # XML to JSON conversion
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            begin_time = root.find('ns:fileHeader/ns:measCollec', config['namespace']).get('beginTime')
            
            for meas_info in root.findall('ns:measData/ns:measInfo', config['namespace']):
                meas_info_id = meas_info.get('measInfoId')
                job_id = meas_info.find('ns:job', config['namespace']).get('jobId')
                gran_period = meas_info.find('ns:granPeriod', config['namespace']).get('duration')
                end_time = meas_info.find('ns:granPeriod', config['namespace']).get('endTime')

                meas_types = {}
                for meas_type in meas_info.findall('ns:measType', config['namespace']):
                    meas_types[meas_type.get('p')] = meas_type.text

                for meas_value in meas_info.findall('ns:measValue', config['namespace']):
                    meas_obj_ldn = meas_value.get('measObjLdn')
                    for r in meas_value.findall('ns:r', config['namespace']):
                        kpi_id = r.get('p')
                        combined_data.append({
                            'measInfoId': meas_info_id,
                            'jobId': job_id,
                            'granPeriod': gran_period,
                            'beginTime': begin_time,
                            'endTime': end_time,
                            'measObjLdn': meas_obj_ldn,
                            'kpiId': kpi_id,
                            'kpiName': meas_types.get(kpi_id, 'Unknown'),
                            'kpiValue': r.text
                        })
            
            # Move processed XML
            processed_path = os.path.join(config['xml_processed_dir'], filename)
            shutil.move(xml_path, processed_path)
            
            # Create XML backup
            backup_filename = os.path.basename(filename)  # Keep original name (e.g., "data.xml")
            backup_path = os.path.join(config['xml_backup_dir'], backup_filename)

	    # Handle duplicates by adding a counter
            counter = 1
            while os.path.exists(backup_path):
                base, ext = os.path.splitext(backup_filename)
                backup_path = os.path.join(config['xml_backup_dir'], f"{base}_{counter}{ext}")
                counter += 1
            shutil.copy2(processed_path, backup_path)
            
            processed_count += 1
            print(f"Processed {filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue
    
    # Write combined JSON file
    if combined_data:
        with open(combined_json_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=4)
        print(f"Created {combined_filename} with {len(combined_data)} records")
    
    return processed_count

def check_files_processed(**kwargs):
    """Determine whether to run Spark or skip"""
    ti = kwargs['ti']
    file_count = ti.xcom_pull(task_ids='process_xml_files')
    return 'spark_to_kafka' if file_count > 0 else 'skip_spark'

# Tasks
setup_dirs = PythonOperator(
    task_id='ensure_directories_exist',
    python_callable=ensure_directories_exist,
    dag=dag,
)

gzip_task = PythonOperator(
    task_id='process_gzip_files',
    python_callable=process_gzip_files,
    dag=dag,
)

xml_task = PythonOperator(
    task_id='process_xml_files',
    python_callable=process_xml_files,
    dag=dag,
)

branch_task = BranchPythonOperator(
    task_id='check_files_processed',
    python_callable=check_files_processed,
    dag=dag,
)

skip_spark = DummyOperator(
    task_id='skip_spark',
    dag=dag,
)

spark_task = SparkSubmitOperator(
    task_id='spark_to_kafka',
    application='/app/mypy/streaming.py',
    conn_id='spark_default',
    packages='org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5',
    conf={
        'spark.sql.streaming.forceDeleteTempCheckpointLocation': 'false',
        'spark.executor.memory': '1g',
        'spark.driver.memory': '1g',
        'spark.executor.instances:' : '1',
        'spark.driver.extraJavaOptions': 
            f'-Djson.input.dir={config["json_output_dir"]} '
            f'-Djson.processed.dir={config["json_processed_dir"]} '
            f'-Djson.backup.dir={config["json_backup_dir"]}'
    },
    dag=dag
)



success_task = DummyOperator(
    task_id='pipeline_success',
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    dag=dag,
)

# Workflow
setup_dirs >> gzip_task >> xml_task >> branch_task
branch_task >> [spark_task, skip_spark]
[spark_task, skip_spark] >>  success_task
