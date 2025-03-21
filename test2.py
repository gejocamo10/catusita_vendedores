import requests
import pandas as pd 

class APIClient:
    def __init__(self, api_url, start_date, end_date, auth_token=None):
        """
        Inicializa la clase con la URL de la API, las fechas y el token de autenticación opcional.
        
        :param api_url: URL de la API.
        :param start_date: Fecha de inicio en formato YYYYMMDD.
        :param end_date: Fecha de fin en formato YYYYMMDD.
        :param auth_token: Token de autenticación opcional (si la API lo requiere).
        """
        self.api_url = api_url
        self.start_date = start_date
        self.end_date = end_date
        self.auth_token = auth_token

    def fetch_data_from_api(self):
        """Obtiene datos desde la API y los convierte en un DataFrame."""
        params = {"Date1": self.start_date, "Date2": self.end_date}
        
        # Headers opcionales
        headers = {
            "Accept": "application/json"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            response = requests.get(self.api_url, params=params, headers=headers)
            response.raise_for_status()  # Lanza error si el código de estado no es 200

            data = response.json().get("data", [])
            if isinstance(data, list):  # Asegurar que data es una lista antes de convertir a DataFrame
                return pd.DataFrame(data)
            else:
                print("Advertencia: La respuesta de la API no contiene una lista válida.")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            return pd.DataFrame()

# ---------------- PRUEBA DEL SCRIPT ----------------

if __name__ == "__main__":
    # Configuración de la API
    API_URL = "http://api.catusita.com:8083/api/sales/forDate"
    START_DATE = "20250101"
    END_DATE = "20250223"
    AUTH_TOKEN = None  # Cambiar por el token si es necesario

    client = APIClient(API_URL, START_DATE, END_DATE, AUTH_TOKEN)
    df = client.fetch_data_from_api()

    if not df.empty:
        print("Datos obtenidos correctamente:")
        print(df.head())
    else:
        print("No se obtuvieron datos.")
