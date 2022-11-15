import pandas as pd
from os import listdir
import os

CUR_DIR = os.path.abspath(os.path.dirname(__file__))


CSV_FILE = 'https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-economia-y-finanzas/buenos-aires-compras/bac_anual.csv'
DOLAR_FILE = 'https://github.com/MGaloto/dash_dolar_blue/blob/main/data/dolarfinal.csv?raw=true'
CSV_FILE_NAME = 'df'
DOLAR_FILE_NAME = 'df_dolar'

class ETL():

    def _extract_data():

        def read_csv_file(file, low_memory=False):
            data = pd.read_csv(file, low_memory=low_memory, index_col=0)
            return data

        def save_csv_file(data, folder, name):
            folder_out =  f"{CUR_DIR}/{folder}/{name}.csv"
            data.to_csv(folder_out,index=False)

        df = read_csv_file(CSV_FILE)
        df_dolar = read_csv_file(DOLAR_FILE)
        save_csv_file(df, 'data_csv',CSV_FILE_NAME)
        save_csv_file(df_dolar, 'data_csv',DOLAR_FILE_NAME)

        path_to_dir = CUR_DIR + '/data_csv'
        filenames = listdir(path_to_dir)
        csv_files = [file for file in filenames if file.endswith(".csv")]
        print('Archivos CSV ya descargados: {}'.format(csv_files))


    def _transform_load_data():
        
        def get_date(value):
            date_list = (value.map(lambda x: str(x).split('T')[0]).values)
            date = pd.to_datetime(date_list, format='%Y-%m-%d')
            return date

        def edit_value(value):
            serie = (value.map(lambda x: str(x).replace(",","").strip().title()).values)
            return serie

        def remove_duplicated(data):
            dataframe = data.loc[:,~data.apply(lambda x: x.duplicated(),axis=1).all()]
            return dataframe

        df = pd.read_csv(f"{CUR_DIR}/data_csv/{CSV_FILE_NAME}.csv", low_memory=False)
        df_dolar = pd.read_csv(f"{CUR_DIR}/data_csv/{DOLAR_FILE_NAME}.csv")[['Fecha','Promedio']].rename(columns = {'Fecha': 'date', 'Promedio': 'tc'})   

        df = remove_duplicated(df)
        df_dolar = remove_duplicated(df_dolar)

        def get_filter_columns(data):
            filter_col = [
                'tender/procuringEntity/name', # El nombre de la parte involucrada al que se hace referencia. Este debe de ser igual al nombre de una entrada en la sección de participantes. (reparticion)
                'contracts/0/items/0/quantity', # El número de unidades requerido. (cantidad)
                'contracts/0/items/0/unit/value/amount', # Monto como una cifra. (precio)
                'tender/items/0/unit/value/currency', # La moneda para cada monto. (moneda)
                'parties/0/roles', # Los roles de las partes involucradas en el proceso de contratación. (operador)
                'tender/additionalProcurementCategories', # Cualquier categoría adicional que describe los objetos de este proceso de contratación. (Rubro)
                'contracts/0/dateSigned', # La fecha en que se firmó el contrato. En el caso de múltiples firmas, la fecha de la última firma. (date)
                'parties/0/name', # Un nombre común para esta organización u otro participante en el proceso de contratación. (entidad)
                'tender/procurementMethodDetails' # Detalles adicionales sobre el método de licitación utilizado. (tipo)
                ]
                
            rename_col = [
                'reparticion', 
                'cantidad', 
                'precio', 
                'moneda', 
                'operador', 
                'rubro', 
                'date', 
                'entidad',
                'tipo']
            dataframe = data[filter_col]
            dataframe.rename(columns = dict(zip(filter_col, rename_col)), inplace = True)
            return dataframe

        def get_join(datauno, datados, index):
            return datauno.join(datados.set_index(index), on=index).sort_values(by = index, ascending = False)


        df = get_filter_columns(df)

        df['reparticion'] = edit_value(df['reparticion'])
        df['reparticion'] = df.apply(lambda x: "Ministerio de Gobierno" if x['reparticion'] == 'Nan' else x['reparticion'], axis=1)

        df['date'] = get_date(df['date'])
        df_dolar['date'] = get_date(df_dolar['date'])

        df['total'] = (df['precio'] * df['cantidad']) / 100000

        df = get_join(df, df_dolar, 'date')

        df['tc'] = df['tc'].fillna(method='bfill')
        df['total'] = df.apply(lambda x: x['total'] * x['tc'] if x['moneda'] == 'USD' else x['total'], axis=1)

        df = df.drop('moneda', axis=1).reset_index(drop=True)

        def get_save_file(data, folder_out):
            data.to_csv(folder_out,index=False, encoding='latin1')

        get_save_file(df.loc[(df['operador']).isin(['buyer;procuringEntity','buyer'])].groupby(['reparticion', 'rubro'], as_index=False)[['reparticion', 'rubro', 'total']].sum().sort_values(by = 'total', ascending = False).reset_index(drop=True),
        f"{CUR_DIR}/home/ejercicio1_all.csv")

        get_save_file(df.loc[(df['operador']).isin(['supplier'])].groupby(['entidad'], as_index=False)[['entidad', 'total']].sum().sort_values(by = 'total', ascending = False).reset_index(drop=True),
        f"{CUR_DIR}/home/ejercicio2_all.csv")

        get_save_file(df.loc[(df['operador']).isin(['buyer;procuringEntity','buyer'])].groupby(['tipo'], as_index=False)[['tipo', 'total']].sum().sort_values(by = 'total', ascending = False).reset_index(drop=True),
        f"{CUR_DIR}/home/ejercicio3_all.csv")

        return 'Load Dataframes'
        