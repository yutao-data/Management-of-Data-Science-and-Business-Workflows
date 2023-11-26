from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
import tarfile
import requests

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=1),
}

dag = DAG('process_web_log',
          default_args=default_args,
          description='DAG for processing web log',
          schedule_interval='@daily',
          catchup=False,
          tags=['DSBW'])

# Update the path to the new location of your log file inside the Docker container
log_dir = '/usr/local/airflow'
log_file = f'{log_dir}/log.txt'
extracted_data_file = f'{log_dir}/extracted_data.txt'
transformed_data_file = f'{log_dir}/transformed_data.txt'
tar_file = f'{log_dir}/weblog.tar'

def scan_for_log(**context):
    if os.path.isfile(log_file):
        return log_file
    else:
        raise ValueError("log.txt not found")

def extract_data(**context):
    task_instance = context['ti']
    log_path = task_instance.xcom_pull(task_ids='scan_for_log')
    
    with open(log_path, 'r') as file, open(extracted_data_file, 'w') as out_file:
        for line in file:
            ip_address = line.split()[0]  # Assuming IP address is the first element in the log line
            out_file.write(ip_address + '\n')

def transform_data(**context):
    with open(extracted_data_file, 'r') as file, open(transformed_data_file, 'w') as out_file:
        for line in file:
            if '198.46.149.143' not in line:
                out_file.write(line)

def load_data(**context):
    with tarfile.open(tar_file, 'w') as tar:
        tar.add(transformed_data_file, arcname='transformed_data.txt')
        
def send_slack_message(**context):
    webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    message = "Workflow executed successfully on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"text": message}
    response = requests.post(webhook_url, json=data)
    print("Message sent to Slack: Status code", response.status_code)

def send_slack_message(**context):
    webhook_url = "https://hooks.slack.com/services/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" 
    message = "Workflow executed successfully on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"text": message}
    response = requests.post(webhook_url, json=data)
    print("Message sent to Slack: Status code", response.status_code)


# Define tasks
scan_task = PythonOperator(
    task_id='scan_for_log',
    python_callable=scan_for_log,
    provide_context=True,
    dag=dag)

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    provide_context=True,
    dag=dag)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,
    dag=dag)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    provide_context=True,
    dag=dag)

success_message_task = PythonOperator(
    task_id='send_success_message',
    python_callable=send_slack_message,  
    provide_context=True,
    dag=dag)


# Set up the workflow
scan_task >> extract_task >> transform_task >> load_task >> success_message_task

