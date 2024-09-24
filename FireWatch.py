import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar a conexão com o banco de dados PostgreSQL
def conectar_banco():
    conn = psycopg2.connect(
        host="localhost",
        database="firewatch",
        user="postgres",
        password="souloko10",
       
    )
    conn.set_client_encoding('latin1')
    return conn

# Função para buscar dados da tabela com cache atualizado
@st.cache_data
def carregar_dados():
    conn = conectar_banco()
    query = "SELECT * FROM firewatch"
    
    # Tentar ler com a codificação 'latin1' ou 'ISO-8859-1' se 'utf-8' falhar
    try:
        df = pd.read_sql(query, conn)
    except UnicodeDecodeError:
        df = pd.read_sql(query, conn, encoding='latin1')

    conn.close()
    
    # Converter as colunas que deveriam ser numéricas
    df['avg_precipitacao'] = pd.to_numeric(df['avg_precipitacao'], errors='coerce')
    df['avg_numero_dias_sem_chuva'] = pd.to_numeric(df['avg_numero_dias_sem_chuva'], errors='coerce')
    df['avg_risco_fogo'] = pd.to_numeric(df['avg_risco_fogo'], errors='coerce')
    df['avg_frp'] = pd.to_numeric(df['avg_frp'], errors='coerce')

    return df

# Carregar os dados
df = carregar_dados()

# Título do dashboard
st.title("Monitoramento de Incêndios Florestais e Seca no Brasil")

# Filtros de pesquisa
st.sidebar.header("Filtros de Pesquisa")
municipio = st.sidebar.multiselect("Selecione o Município", df['municipio'].unique())
estado = st.sidebar.multiselect("Selecione o Estado", df['estado'].unique())
bioma = st.sidebar.multiselect("Selecione o Bioma", df['bioma'].unique())

# Aplicar filtros
if municipio:
    df = df[df['municipio'].isin(municipio)]

if estado:
    df = df[df['estado'].isin(estado)]

if bioma:
    df = df[df['bioma'].isin(bioma)]

# Exibir a tabela filtrada
st.write("### Dados Filtrados (última atualização 24/09/2024)")
st.dataframe(df)

from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static


# Função para obter coordenadas (latitude, longitude) a partir do nome da cidade e estado
def obter_coordenadas(cidade, estado):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(f"{cidade}, {estado}, Brasil")
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

# Função para mapear as cores com base no risco de fogo
def cor_risco_fogo(risco):
    if risco < 50:
        return "#00BFFF"  # Azul
    elif risco < 75:
        return "#FFA500"  # Laranja
    else:
        return "#FF0000"  # Vermelho

# Carregar os dados
df = carregar_dados()

# Criar o mapa centrado no Brasil
m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4)

# Adicionar os pontos ao mapa
for index, row in df.iterrows():
    coordenadas = obter_coordenadas(row['municipio'], row['estado'])
    if coordenadas:  # Apenas adicionar se as coordenadas forem encontradas
        risco = row['avg_risco_fogo']
        folium.CircleMarker(
            location=coordenadas,
            radius=5,
            color=cor_risco_fogo(risco),
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['municipio']} - Risco: {risco}"
        ).add_to(m)

# Exibir o mapa no Streamlit
st.title("Mapa de Risco de Incêndio")
folium_static(m)
