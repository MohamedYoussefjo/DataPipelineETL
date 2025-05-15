from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.sensors.filesystem import FileSensor

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'csv_to_kafka',
    default_args=default_args,
    description='Process CSV files to Kafka and move processed files',
    schedule_interval=None, 
    catchup=False,
    max_active_runs=1,
)

spark_job = SparkSubmitOperator(
    task_id='process_csv_to_kafka',
    application='/app/mypy/preprocessproduce.py',  
    conn_id='spark_default',
    verbose=True,
    conf={
        'spark.jars.packages': 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5',
        "spark.executor.cores": "4",
        "spark.executor.memory": "3g",
    },
    dag=dag,
)

# Optional: Add a sensor to check if files exist before processing



spark_job
