from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    '6gbfiletokafka',
    default_args=default_args,
    description='Process CSV files to Kafka and move processed files',
    schedule_interval='*/30 * * * *', # Runs once per day
    catchup=False,
    max_active_runs=1,
)

spark_job = SparkSubmitOperator(
    task_id='process_csv_to_kafka',
    application='/app/mypy/preprocessproduce.py',  # Update this path
    conn_id='spark_default',
    verbose=True,
    conf={
        'spark.jars.packages': 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5',
        'spark.driver.memory': '1g',
        'spark.executor.memory': '1g',
        'spark.executor.cores': '1',
        'spark.executor.instances': '1',
        'spark.sql.streaming.checkpointLocation': '/app/checkpoint1firstcsv',
    },
    dag=dag,
)

# Optional: Add a sensor to check if files exist before processing
from airflow.sensors.filesystem import FileSensor

file_sensor = FileSensor(
    task_id='check_for_files',
    filepath='/app/inputcsv/*.csv',  # Adjust pattern as needed
    poke_interval=60,  # Check every 60 seconds
    timeout=3600,  # Timeout after 1 hour
    mode='reschedule',
    dag=dag,
)

file_sensor >> spark_job
