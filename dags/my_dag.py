try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from datetime import timedelta, datetime
    from airflow.utils.dates import days_ago
    from etl import ETL
except Exception as e:
    print('Error {}'.format(e))



def extract():
    print('Extract Data..')
    ETL._extract_data()
    

def transform_load():
    print('Transform and Load Data..')
    return ETL._transform_load_data()


with DAG(
    dag_id='dag', # nombre del dag
    default_args={
    'owner':'airflow',
    'depends_on_past' : False,
    'retries' : 1, # reintentos si falla
    'retry_delay' : timedelta(minutes=1) # segundos entre reintentos
    },
    schedule_interval="@once", 
    start_date=datetime(2022, 11, 9)
) as dag:

    extract_task = PythonOperator(task_id='extract', python_callable=extract)
    transform_load_task = PythonOperator(task_id='transform_load', python_callable=transform_load)

    extract_task >> transform_load_task # Se utilizan bitshift operators.

