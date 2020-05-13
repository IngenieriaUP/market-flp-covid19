import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pydeck as pdk

@st.cache
def read_data(fp):
    gdf = gpd.read_file(fp)
    return gdf

st.title('Análisis de ubicación de mercados móviles')

st.write('Problema de aglomeracion de personas en el mercado, solucion viable es colocas mas maercado (fromato de itinerates')

st.write('como sabnemos que la ubicacion es opmitima, de que depende donde ubicarlos? por que ubicarlos en un determinado espacio?')

st.write('''

La correcto ubicacion depende de que:
1. mejore la accesibilidad a los mercados (medimos con tiempo y distancia de viaje)
-> mapa
2. considerando la necesidad de mantener distancia social debemos incluir en el analisis la
 distribucion de la densidad poblacional en la zona geografica
-> mapa
''')

st.write('''
Para solucionar este problemade ubicacion se ha usado un MOdleo de localizacion optima instalaciones


0. se aplicó la primera prueba para distritios adebido a que cada municipalidad dsitrital
 tiene la facultad de implementar los mercaods itinerantes

1. Fuente de datos
-> Urbapy(Pobalcion HDX FB, Limites OSM, Censo de Mercados INEI, POIS de Overpas OSM)

2. Preprocesaminto 
Formato a los datos para el modelo

3. Procesamiento
que hace el modelo ? minimizar la distacia crespentadfo lazs restrs.
que podria salir mal? consideraciones

4. Resultados 
-> Mapa
-> df las direcciones
-> % De gente asignado a cada instalacion ()
-> Distancia y duracion (comparacion de escenarios)
-> discusion (se puede mejorar asi asa, etc, falta el flujo real de gente en el mercado)
''')



fps_options = {
    'San Juan de Lurigancho': 'inputs/flp_sjl/selected_facilities_sjl.shp',
    'Miraflores': 'inputs/flp_miraflores/selected_facilities_mf.shp'
}

selected_district = st.selectbox(
    '¿Qué distrito quieres ver?',
    list(fps_options.keys())
)

data = read_data(fps[selected_district])
active_markets = data[data['active'] == 1]

st.subheader("Mapa de mercados")

st.map(active_markets)


if st.checkbox('Muestra los datos'):
    st.subheader('Datos de mercados')
    st.write(pd.DataFrame(data.iloc[:,:-1]))

