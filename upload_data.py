import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Crear engine SQLAlchemy
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)

# Leer archivo CSV generado por CatusitaSalesProcessor
df = pd.read_csv("catusita_sales.csv")
df['fecha'] = pd.to_datetime(df['fecha'])

# Cargar en la tabla public.ventas (se reemplaza si ya existe)
df.to_sql('ventas', engine, schema='public', if_exists='replace', index=False)

print("✅ Datos cargados exitosamente en la tabla public.ventas.")
