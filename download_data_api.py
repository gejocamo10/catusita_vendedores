import requests
import pandas as pd
import os
from datetime import datetime, timedelta

def download_monthly_data(start_date: str, end_date: str, url: str, auth_token: str = None):
    """
    Descarga datos desde la API para el rango de fechas especificado, incluyendo headers opcionales.
    
    :param start_date: Fecha de inicio en formato 'YYYYMMDD'
    :param end_date: Fecha de fin en formato 'YYYYMMDD'
    :param url: URL de la API
    :param auth_token: Token Bearer opcional
    :return: DataFrame con los datos
    """
    params = {"Date1": start_date, "Date2": end_date}

    # Agregar headers
    headers = {
        "Accept": "application/json"
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Lanza excepción si no es 200

        data = response.json().get("data", [])
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            print(f"⚠️ La respuesta de la API no contiene una lista válida para {start_date} - {end_date}")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la solicitud para {start_date} - {end_date}: {e}")
        return pd.DataFrame()

def concatenate_monthly_data(start_date, end_date):
    """
    Descarga los datos mensualmente desde 2022-01-01 hasta la fecha actual.
    """
    url = "http://api.catusita.com:8083/api/sales/forDate"
    # start_date = datetime(2021, 1, 1)
    # end_date = datetime.today()
    
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
    all_data.to_csv("data/process/df_sales.csv", index=False)
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

    df.to_csv("data/process/df_sales.csv", index=False)
    print("Limpieza completa. Datos guardados en df_sales.csv")
    return df

def merge_with_metas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Une el DataFrame de ventas con las metas en base a 'fuente_suministro'.
    """
    metas_path = os.path.join("data", "raw", "catusita", "metas.xlsx")

    if not os.path.exists(metas_path):
        raise FileNotFoundError(f"No se encontró el archivo de metas: {metas_path}")

    metas_df = pd.read_excel(metas_path)

    if "fuente_suministro" not in df.columns:
        raise KeyError("La columna 'fuente_suministro' no está en los datos de ventas.")
    if "fuente_suministro" not in metas_df.columns:
        raise KeyError("La columna 'fuente_suministro' no está en el archivo de metas.")

    print("🔄 Realizando merge con archivo de metas...")
    merged_df = df.merge(metas_df, on="fuente_suministro", how="left")

    for col in ["familia", "segmento", "marca", "gestor"]:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna("Desconocido")
    if "meta" in merged_df.columns:
        merged_df["meta"] = merged_df["meta"].fillna(0)

    return merged_df

def read_and_clean_old_data(file_path):
    """Lee y combina todas las hojas de un archivo Excel, renombrando las columnas según la imagen."""
    # Diccionario con los nuevos nombres de columnas
    column_mapping = {
        "CIA": "cia",
        "Fecha": "fecha",
        "Cliente": "cliente",
        "Nombre Cliente": "nombre_cliente",
        "Rubro": "rubro",
        "Departamento": "departamento",
        "Documento": "documento",
        "Artículo": "articulo",
        "Nombre de Artículo": "nombre_articulo",
        "Fuente de Suministro": "fuente_suministro",
        "Cantidad": "cantidad",
        "Venta $": "venta_usd",
        "Venta S/.": "venta_pen",
        "Costo": "costo",
        "Nombre Vendedor": "nombre_vendedor",
        "Cobrador": "cobrador"
    }
    df_catusita = pd.read_excel(file_path, sheet_name="Sheet1")
    lista_columnas = df_catusita.columns.tolist()
    excel_file = pd.ExcelFile(file_path)
    list_hojas = excel_file.sheet_names[1:]
    for hoja in list_hojas:
        df_catusita_hoja = pd.read_excel(file_path, sheet_name=hoja, header=None)
        df_catusita_hoja.columns = lista_columnas
        df_catusita = pd.concat([df_catusita, df_catusita_hoja], ignore_index=True)
    df_catusita.rename(columns=column_mapping, inplace=True)
    return df_catusita

if __name__ == "__main__":
    print("comenzando")
    start_date = datetime(2021, 1, 1)
    end_date = datetime.today() - timedelta(days=1)
    concatenate_monthly_data(start_date, end_date)
    
    df_cleaned = clean_sales_data("data/process/df_sales.csv")
    df_enriched = merge_with_metas(df_cleaned)
    
    df_enriched.to_csv("data/process/catusita_sales.csv", index=False)
    print("✅ Proceso completado. Archivo guardado como catusita_sales.csv")

    # df_antiguo = read_and_clean_old_data("Data de venta 01.01.21 a 06.12.24.xls")
    # df_antiguo.to_csv("df_antiguo.csv", index=False, encoding="utf-8-sig")
