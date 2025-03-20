import requests
import pandas as pd
from datetime import datetime, timedelta

def download_monthly_data(start_date: str, end_date: str, url: str):
    """
    Descarga datos desde la API para el rango de fechas especificado.
    """
    params = {"Date1": start_date, "Date2": end_date}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        return pd.DataFrame(data)
    else:
        print(f"Error en la solicitud para {start_date} - {end_date}: {response.status_code}")
        return pd.DataFrame()

def concatenate_monthly_data():
    """
    Descarga los datos mensualmente desde 2022-01-01 hasta la fecha actual.
    """
    url = "http://api.catusita.com:8083/api/sales/forDate"
    start_date = datetime(2022, 1, 1)
    end_date = datetime.today()
    
    all_data = pd.DataFrame()
    
    current_date = start_date
    while current_date < end_date:
        # Calcular el último día del mes actual
        next_month = current_date.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        
        # Si el mes final excede la fecha actual, ajustar la fecha final
        if last_day_of_month > end_date:
            last_day_of_month = end_date
        
        # Convertir fechas a formato YYYYMMDD
        start_str = current_date.strftime("%Y%m%d")
        end_str = last_day_of_month.strftime("%Y%m%d")
        
        print(f"Descargando datos de {start_str} a {end_str}...")
        monthly_data = download_monthly_data(start_str, end_str, url)
        
        # Concatenar datos descargados
        all_data = pd.concat([all_data, monthly_data], ignore_index=True)
        
        # Avanzar al siguiente mes
        current_date = last_day_of_month + timedelta(days=1)
    
    # Guardar los datos en un CSV
    all_data.to_csv("df_sales.csv", index=False)
    print("Descarga completa. Datos guardados en df_sales.csv")

def clean_sales_data(file_path):
    """
    Carga, limpia y transforma el archivo de ventas descargado desde la API.
    """
    # Cargar el archivo CSV
    df = pd.read_csv(file_path)
    
    # Renombrar columnas
    column_mapping = {
        "dateDocument": "fecha",
        "document": "documento",
        "codeArticle": "articulo",
        "nameArticle": "nombre_articulo",
        "codeSupply": "codigo",
        "nameSupply": "fuente_suministro",
        "codeClient": "cliente",
        "nameClient": "nombre_cliente",
        "rucClient": "ruc_cliente",
        "codeSeller": "vendedor",
        "nameSeller": "nombre_vendedor",
        "quantity": "cantidad",
        "amountSOL": "venta_pen",
        "amountUSD": "venta_usd",
        "cost": "costo"
    }
    df.rename(columns=column_mapping, inplace=True)
    
    # Convertir la columna de fecha a formato datetime
    df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
    
    # Verificar si hay fechas inválidas
    invalid_dates = df[df["fecha"].isna()]
    if not invalid_dates.empty:
        print("Advertencia: Se encontraron fechas inválidas.")
        print(invalid_dates)
    
    # Convertir ruc_cliente a string (para evitar tipos mixtos)
    df["ruc_cliente"] = df["ruc_cliente"].astype(str)
    
    # Crear columna de tipo de transacción
    df["tipo_transaccion"] = "venta"
    df.loc[df[["cantidad", "venta_pen", "venta_usd", "costo"]].lt(0).any(axis=1), "tipo_transaccion"] = "devolucion"
    
    return df

if __name__ == "__main__":
    # concatenate_monthly_data()
    df_cleaned = clean_sales_data("df_sales.csv")
    df_cleaned.to_csv("df_sales_cleaned.csv", index=False)
