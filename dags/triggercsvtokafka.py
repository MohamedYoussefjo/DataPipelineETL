from datetime import datetime
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

dag = DAG(
    'file_arrival_sensor',
    schedule_interval=None,  # Manual or external trigger
    start_date=datetime(2025, 4, 15),
    catchup=False,
    is_paused_upon_creation=True,
)

file_sensor = FileSensor(
    task_id='wait_for_new_csv',
    filepath='/app/csv/inputcsv/*.csv',  # Adjust path
    poke_interval=10,  # Check every 10 seconds
    timeout=3600 * 24,  # Keep running indefinitely
    mode='poke',
    dag=dag,
)

trigger_processing = TriggerDagRunOperator(
    task_id='trigger_csv_to_kafka',
    trigger_dag_id='csv_to_kafka',  # Your processing DAG
    dag=dag,
)

file_sensor >> trigger_processing