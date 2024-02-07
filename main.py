from flask import Flask, jsonify, render_template, send_from_directory, json
import os
from shareplum import Office365, Site
from shareplum.site import Version
import pandas as pd
from io import BytesIO

app = Flask(__name__, static_url_path='')
sp_server_url = os.getenv('SP_SITE') 
sp_site_url = os.getenv('SP_SITE_PATH') 
sp_username = os.getenv('SP_USER')
sp_password = os.getenv('SP_PWD')
sp_list_name = os.getenv('SP_LIST_NAME')
# Reemplaza con la URL real de tu archivo Excel en SharePoint

def GetDataFromFile():
    
    try:
        
        authcookie = Office365(sp_server_url, username=sp_username, password=sp_password).GetCookies()        
        path = sp_server_url+sp_site_url
        site = Site(path, version=Version.v2016, authcookie=authcookie)
        sp_folder = site.Folder('Documentos compartidos/Llaves')
        print(sp_username)
        print('---OK')
        if sp_folder:
        # La lista tiene elementos, ahora puedes acceder a ellos
            xls = sp_folder.get_file('Libro de llaves.xlsx')
            print('SP_FOLDER')
            with open("Libro_de_llaves.xlsx", "wb") as fh:
                fh.write(xls)
                print('---')

            data = DataFromXls()
        
        print("data", len(data))
        return data
    
    except Exception as e:
         print(f"FileService.GetOperatorsFromSharepoint error: " + str(e))

def DataFromXls():
    try:
            
        df = pd.read_excel('Libro_de_llaves.xlsx', sheet_name='Form1')
        df.to_csv('libro.csv', index=False)

        data = pd.read_csv('libro.csv')

        # Convierte las columnas de fecha a tipo datetime
        data['Hora de inicio'] = pd.to_datetime(data['Hora de inicio'])
        data['Hora de finalización'] = pd.to_datetime(data['Hora de finalización'])
        data['Hora de la última modificación'] = pd.to_datetime(data['Hora de la última modificación'])

        # Filtra las filas donde la acción es 'Retiro' o 'Devolución'
        df_retiro_devolucion = data[data['Acción2'].isin(['Retiro de llave', 'Devolución de llave'])]

        # Encuentra la fila con la hora de finalización máxima para cada llave
        indices_ultimas_retiro_devolucion = df_retiro_devolucion.groupby('Llave3')['Hora de finalización'].idxmax()

        # Selecciona las filas correspondientes a las últimas acciones de retiro o devolución
        df_ultimas_retiro_devolucion = df_retiro_devolucion.loc[indices_ultimas_retiro_devolucion]

        # Filtra solo las llaves3 que tienen como última acción2 el retiro de llaves
        df_resultado = df_ultimas_retiro_devolucion[df_ultimas_retiro_devolucion['Acción2'] == 'Retiro de llave']

        # Selecciona solo las columnas requeridas
        df_resultado = df_resultado[['Llave3', 'Responsable', 'Empresa', 'Telefono de contacto']]

        # Muestra el resultado
        print(df_resultado)

        os.remove('libro.csv')
        os.remove('Libro_de_llaves.xlsx')

        return df_resultado

    except Exception as e:
        print(f"main.DataFromXls error: " + str(e))

@app.route('/static/<path:filename>')
def staticfiles(filename):
    GetDataFromFile()
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

@app.route('/')
def obtener_llaves():
    data = GetDataFromFile()
    # Convierte el DataFrame a JSON
    json_resultado = data.to_json(orient='records', default_handler=str)
    # Convierte la cadena JSON interna a un objeto Python
    resultado_dict = json.loads(json_resultado)
    # Usa jsonify para enviar la respuesta JSON
    return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html')
    return jsonify({"resultado": resultado_dict})
     
@app.route('/api/llaves', methods=['GET'])
def obtener_datos_llaves():
    data = GetDataFromFile()
    # Convierte el DataFrame a JSON
    json_resultado = data.to_json(orient='records', default_handler=str)
    # Convierte la cadena JSON interna a un objeto Python
    resultado_dict = json.loads(json_resultado)
    # Usa jsonify para enviar la respuesta JSON
    return jsonify({"resultado": resultado_dict})

if __name__ == '__main__':
    app.run(debug=False, port=5010)
   