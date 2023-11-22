from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
import tarfile

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 11, 22),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('process_web_log',
          default_args=default_args,
          description='Process web log file',
          schedule_interval=timedelta(days=1))

def scan_for_log():
    log_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/log.txt'
    if os.path.exists(log_path):
        return True
    else:
        raise ValueError("log.txt not found")

def extract_data():
    log_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/log.txt'
    extracted_data_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/extracted_data.txt'

    with open(log_path, 'r') as file:
        lines = file.readlines()

    ip_addresses = [line.split()[0] for line in lines] # Assuming IP is the first element
    with open(extracted_data_path, 'w') as file:
        for ip in ip_addresses:
            file.write(ip + '\n')

def transform_data():
    extracted_data_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/extracted_data.txt'
    transformed_data_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/transformed_data.txt'

    with open(extracted_data_path, 'r') as file:
        data = file.readlines()

    data = [ip for ip in data if ip.strip() != '198.46.149.143']

    with open(transformed_data_path, 'w') as file:
        for ip in data:
            file.write(ip)

def load_data():
    transformed_data_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/transformed_data.txt'
    tar_path = '/home/cyt/ULB/DSBW/Management-of-Data-Science-and-Business-Workflows/Assignment_3/weblog.tar'

    with tarfile.open(tar_path, 'w') as tar:
        tar.add(transformed_data_path, arcname='transformed_data.txt')

scan_task = PythonOperator(
    task_id='scan_for_log',
    python_callable=scan_for_log,
    dag=dag)

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag)

scan_task >> extract_task >> transform_task >> load_task

