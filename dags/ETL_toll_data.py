from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import pandas as pd


# Default arguments
default_args = {
    'owner': 'quan',
    'start_date': datetime(2024, 6, 10),
    'email': ['21521333@gm.uit.edu.vn'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Initialize the DAG
dag = DAG(
    'ETL_toll_data',
    default_args=default_args,
    description='Apache Airflow Final Assignment',
    schedule_interval='@daily',
)

download_data = BashOperator(
    task_id='download_data',
    bash_command='curl -o /tmp/tolldata.tgz https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DB0250EN-SkillsNetwork/labs/Final%20Assignment/tolldata.tgz',
    dag=dag,
)

# Task 1.3 - Create a task to unzip data
unzip_data = BashOperator(
    task_id='unzip_data',
    bash_command='tar -xzvf /tmp/tolldata.tgz -C /tmp',
    dag=dag,
)

# Task 1.4 - Create a task to extract data from csv file
def extract_csv():
    df = pd.read_csv('/tmp/vehicle-data.csv', header=None)
    df.columns = ['Rowid', 'Timestamp', 'Anonymized Vehicle number', 'Vehicle type', 'Number of axles', 'Vehicle code']
    selected_columns = df[['Rowid', 'Timestamp', 'Anonymized Vehicle number', 'Vehicle type']]
    selected_columns.to_csv('/tmp/csv_data.csv', index=False)

extract_data_from_csv = PythonOperator(
    task_id='extract_data_from_csv',
    python_callable=extract_csv,
    dag=dag,
)

# Task 1.5 - Create a task to extract data from tsv file
def extract_tsv():
    df = pd.read_csv('/tmp/tollplaza-data.tsv', sep='\t', header=None)
    df.columns = ['Rowid', 'Timestamp', 'Anonymized Vehicle number', 'Vehicle type', 'Number of axles', 'Tollplaza id', 'Tollplaza code']
    selected_columns = df[['Rowid', 'Number of axles', 'Tollplaza id', 'Tollplaza code']]
    selected_columns.to_csv('/tmp/tsv_data.csv', index=False)

extract_data_from_tsv = PythonOperator(
    task_id='extract_data_from_tsv',
    python_callable=extract_tsv,
    dag=dag,
)

# Task 1.6 - Create a task to extract data from fixed width file
def extract_fixed_width():
    colspecs = [(0, 6), (6, 24), (24, 44), (44, 49), (49, 57), (57, 62), (62, 67)]  # Adjust these based on the file format
    df = pd.read_fwf('/tmp/payment-data.txt', colspecs=colspecs, header=None)
    df.columns = ['Rowid', 'Timestamp', 'Anonymized Vehicle number', 'Tollplaza id', 'Tollplaza code', 'Type of Payment code', 'Vehicle Code']
    selected_columns = df[['Rowid', 'Type of Payment code', 'Vehicle Code']]
    selected_columns.to_csv('/tmp/fixed_width_data.csv', index=False)

extract_data_from_fixed_width = PythonOperator(
    task_id='extract_data_from_fixed_width',
    python_callable=extract_fixed_width,
    dag=dag,
)

# Task 1.7 - Create a task to consolidate data extracted from previous tasks
def consolidate_data():
    df_csv = pd.read_csv('/tmp/csv_data.csv')
    df_tsv = pd.read_csv('/tmp/tsv_data.csv')
    df_fixed_width = pd.read_csv('/tmp/fixed_width_data.csv')

    df_final = pd.merge(df_csv, df_tsv, on='Rowid')
    df_final = pd.merge(df_final, df_fixed_width, on='Rowid')
    df_final.to_csv('/tmp/extracted_data.csv', index=False)

consolidate_data_task = PythonOperator(
    task_id='consolidate_data',
    python_callable=consolidate_data,
    dag=dag,
)

# Task 1.8 - Transform and load the data
def transform_data():
    df = pd.read_csv('/tmp/extracted_data.csv')
    df['Vehicle type'] = df['Vehicle type'].str.upper()
    df.to_csv('/tmp/transformed_data.csv', index=False)

transform_data_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

# Task 1.9 - Define the task pipeline
download_data >> unzip_data >> extract_data_from_csv >> extract_data_from_tsv >> extract_data_from_fixed_width >> consolidate_data_task >> transform_data_task
