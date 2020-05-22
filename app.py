import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

@st.cache
def read_geojson(fp):
    gdf = gpd.read_file(fp, driver='GeoJSON')
    return gdf

st.title('Análisis de ubicación de mercados itinerantes')


# Problema de aglomeracion de personas en el mercado, solucion viable es colocas mas mercados (itinerates)
st.write('''
Desde el inicio del Estado de Emergencia en nuestro país los mercados han recibido un gran volumen de personas.
Esto ha generado que se conviertan en uno de los principales focos de contagio para la población. Por este motivo 
**la Municipalidad de Lima propuso la implementación de mercados itinerantes para aumentar la oferta de mercados y 
reducir la aglomeración de personas.**
''')

# como sabnemos que la ubicacion es opmitima, de que depende donde ubicarlos? por que ubicarlos en un determinado espacio?
st.write('''
En este sentido, **el presente análisis tiene como objetivo hallar la localizacion óptima de los mercados itinerantes.**
Pero antes de lograr este objetivo debemos hacer algunas preguntas: **¿Cómo determinamos si una ubicación es óptima?** 
¿De qué depende esta ubicación? ¿Por qué una ubicacion podría ser mejor que otra? A continuación responderemos estas preguntas.
''')

# 1. mejore la accesibilidad a los mercados (medimos con tiempo y distancia de viaje)
# 2. considerando la distancia social debemos incluir en el analisis de la densidad poblacional en la zona geografica
st.write('''
Luego de realizar un análisis de datos con el equipo multidisciplinario de la Municipalidad Lima y la Universidad del Pacífico 
se llegó a la conclusión de que se debían considerar principalmente las siguientes variables: 

- Accesibilidad del mercado
- Densidad poblacional alrededor del mercado
- Aforo del mercado
- Flujo de personas en el mercado (por hora)
- Posibles lugares para colocar los mercados itinerantes (Por ejemplo parques y losas deportivas)

Esto significa que la situación ideal sería que 
**la duración y distancia de viaje caminando hacia el mercado sea la mínima posible.**
Por ejemplo podemos ver cómo varía la duración (en minutos) del viaje hacia el mercado 
más cercano en el distrito de San Juan de Lurigancho:
''')

sjl_hexs = read_geojson('inputs/sjl_hex.geojson')

fig_durations = px.choropleth_mapbox(
    sjl_hexs.reset_index(), geojson=sjl_hexs.geometry.__geo_interface__, locations='index', 
    color='dur_nn_market_walk',
    color_continuous_scale='magma_r',
    mapbox_style="carto-positron",
    zoom=11, 
    center = {
       "lat": sjl_hexs.geometry.unary_union.centroid.y,
       "lon": sjl_hexs.geometry.unary_union.centroid.x
    },
    opacity=0.3,
    labels={
        'dur_nn_market_walk': 'Duración',
        'dist_nn_market_walk': 'Distancia',
        'n_markets': '# de mercados'
    },
    hover_data = ['dur_nn_market_walk', 'dist_nn_market_walk', 'n_markets']
)
fig_durations.update_layout(mapbox_bearing=-50, 
                  margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(fig_durations, use_container_width=True)

st.write('''
Además, **la cantidad de mercados** ubicados en una zona geografica **debería ser acorde a la densidad poblacional.**
Asimismo, **el flujo de personas** en el mercado debe estar **restringido por el aforo** para 
que sea posible **mantener la distancia social.** Por ejemplo podemos ver la densidad poblacional (número de personas) dentro del 
distrito de San Juan de Lurigancho:
''')

fig_population = px.choropleth_mapbox(
    sjl_hexs.reset_index(), geojson=sjl_hexs.geometry.__geo_interface__, locations='index', 
    color='population_2020',
    color_continuous_scale='viridis',
    mapbox_style="carto-positron",
    zoom=11, 
    center = {
       "lat": sjl_hexs.geometry.unary_union.centroid.y,
       "lon": sjl_hexs.geometry.unary_union.centroid.x
    },
    opacity=0.3,
    labels={
        'population_2020': 'Población',
        'n_markets': '# de mercados'
    },
    hover_data = ['n_markets']
)
fig_population.update_layout(mapbox_bearing=-50, 
                  margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_population, use_container_width=True)

# Para solucionar este problema de ubicación se ha usado un Modelo de localización óptima instalaciones
st.write('''
Por otro lado **los datos de flujos de personas se podrían obtener a partir de fuentes privadas como empresas 
de telecomunicaciones o específicamente Google**. Sin embargo aún no tenemos acceso esa información.
''')

# 0. se aplicó la primera prueba para distritios adebido a que cada municipalidad dsitrital tiene la facultad de implementar los mercaods itinerantes
st.subheader('¿Cómo resolveremos el problema?')
st.write('''
Para resolver la pregunta de dónde es la ubicación óptima para los mercados **contamos con la 
densidad poblacional y la duracion del viaje**. Asi pues, podemos recurrir a modelos de optimización utilizados en el 
área de la logística. Por ejemplo **el modelo de opmitización de localización de instalaciones** (FLP, por sus siglas 
en inglés) permite minimizar los costos de transporte al tiempo que considera factores como la demanda. En este caso
**vamos a minizar la distancia recorrida por las personas hacia los mercados considerando que la cantidad de personas 
que asistan a cada mercado no sobrepase su aforo.** A modo de prueba de concepto hemos aplicado dicho modelo 
en el distrito de San Juan de Lurigancho. 
''')

# 2. Preprocesaminto: Formato a los datos para el modelo

st.subheader('Preprocesamiento de datos')
st.write('''
Primero, se descargaron límites distritales y se dividió el espacio geográfico en hexágonos de ≈0.10km2. Luego se obtuvieron
los datos poblacionales en una resolución de 30x30m, estos datos los usamos como un estimado de la cantidad de clientes.
Después mediante la ubicación de los parques y losas deportivas de cada distrito, construimos nuestro conjunto de 
mercados itinerantes potenciales. Asimismo, sólo se consideraron parques y losas con un área que permita tener un aforo
 de 500 considerando el distanciamiento social necesario. Utilizando tanto los mercados actuales, mercados potenciales y los hexágonos se contruyó
una **matriz de distancia** que nos indica cuanto se demora una persona caminando para movilizarse de cualquier hexágono 
a cualquier mercado.

Con respecto al aforo de los mercados debido que no está reportado en el censo, lo tuvimos que estimar a partir del
área construida de cada mercado. Este valor sirve para restringir la cantidad de personas que pueden ser 
asignadas a un mercado. Por otro lado **el modelo necesita que le digamos el número total de mercados 
itinerantes que se activarán**, para ello la Municipalidad nos indicó que la capacidad logística de los distritos en promedio
podría alcanzar para implementar **~11 mercados itinerantes** en un mes.

En resumen se han calculado las siguientes variables que el modelo necesita:

- Matriz de distancia mercado-clientes (filas-columnas)
- Aforo de cada mercado
- Número de instalaciones a activar (según la capacidad logística de cada distrito)
''') 

# 3. Procesamiento: que hace el modelo ? minimizar la distacia crespentadfo lazs restrs.
# que podria salir mal? consideraciones

st.write('''
Finalmente el modelo retorna dos resultados: 
- La ubicación de los nuevos mercados itinerantes que se deben implementar
- La población que debe ser atendida por los mercados (restringido por el aforo)
''')

st.subheader('Resultados ')
st.write('''
En el siguiente mapa podrás visualizar las ubicaciones seleccionadas de los mercados potenciales y 
la ubicación de los mercados actuales.
''')

# TODO: Add Miraflores
# fps_options = {
#    'San Juan de Lurigancho': 'inputs/flp_sjl/selected_facilities_sjl.shp',
#    'Miraflores': 'inputs/flp_miraflores/selected_facilities_mf.shp'
# }
# selected_district = st.selectbox(
#     '¿Qué distrito quieres ver?',
#     list(fps_options.keys())
# )

sjl_old_markets_merged = read_geojson('inputs/sjl_old_markets_merged.geojson')
active_temporal_markets_poly = read_geojson('inputs/active_temporal_markets_poly.geojson')

# Mapa
st.subheader("Mapa de mercados")
fig = go.Figure()

fig.add_trace(
    go.Scattermapbox(
        name='Mercados',
        customdata=sjl_old_markets_merged[['NOMBRE_MERCADO', 'aforo']],
        lat=sjl_old_markets_merged.lat,
        lon=sjl_old_markets_merged.lon,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=sjl_old_markets_merged['aforo_scaled'],
            sizemin=10,
            color='orange',
            opacity=0.5,
        ),
        line={'color': 'black', 'width':50},
        hovertemplate='Nombre:%{customdata[0]} <br><b>Aforo:%{customdata[1]}} ',
        showlegend=True,
    )
)

fig.add_trace(
    go.Choroplethmapbox(
        name='Potenciales mercados itinerantes',
        customdata=active_temporal_markets_poly['address'],
        geojson=active_temporal_markets_poly.geometry.__geo_interface__,
        locations=active_temporal_markets_poly.index, z=active_temporal_markets_poly.is_active,
        colorscale=[[0, 'rgb(0,255,0)'], [1,'rgb(0,255,0)']],
        showscale=False, 
        showlegend=True,
        marker_opacity=1, marker_line_width=3, marker_line_color='rgb(0,200,0)',
        hovertemplate='Dirección:%{customdata}',
    )
)

fig.update_layout(
    legend={'orientation': 'h'},
    mapbox=dict(
        center=dict(
            lat=sjl_old_markets_merged.geometry.unary_union.centroid.y,
            lon=sjl_old_markets_merged.geometry.unary_union.centroid.x,
        ),
        pitch=0,
        bearing=-50,
        zoom=11,
        style='carto-positron'
    ),
    margin={"r":0,"t":0,"l":0,"b":0}
)

st.plotly_chart(fig, use_container_width=True)

# df las direcciones
address_df = active_temporal_markets_poly[['lat', 'lon', 'address']]
if st.checkbox('Muestra los datos de los potenciales mercados'):
    st.subheader('Ubicación de potenciales mercados itinerantes ')
    st.write(address_df)

st.write('''
Como se puede observar **se ha recomendado* colocar un gran número de mercados itinerantes (5 de 11) en 
la zona suroeste del distrito debido a la alta concentración de personas.** Asimismo, los mercados potenciales 
seleccionados **cubren una zona central en el distrito que no cuenta con mercados cercanos actualmente.**
''') 

# Discusión
st.write('''
También es importante mencionar que estos resultados pueden mejorarse con acceso a datos de movilidad de personas
y la aplicación de un mayor número de restricciones al modelo de optmización para lograr **describir mejor la realidad**.
Por otro lado, es importantísimo el trabajo de **comunicación y concientización de la población** para que se logren los 
resultados esperados.''')

st.subheader('Pasos a seguir')
st.write('''
- Reportar métricas de accesibilidad y volumen de consumidores.
- Ampliar el análisis a más distritos.
- Obtener datos de movilidad de personas.
''')

# TODO: % De gente asignado a cada instalacion ()
# TODO: Distancia y duracion (comparacion de escenarios)


# 1. Fuente de datos: Urbapy(Pobalcion HDX FB, Limites OSM, Censo de Mercados INEI, POIS de Overpas OSM)
st.subheader('Fuentes de datos')
st.write('''
Se utilizaron las siguientes fuentes de datos:

- [Peru: High Resolution Population Density Maps + Demographic Estimates](https://data.humdata.org/dataset/peru-high-resolution-population-density-maps-demographic-estimates)
- [Límites disritales del Servicio Nominatim de Open Street Maps (OSM)](https://nominatim.openstreetmap.org/)
- [Geolocalización de parques y losas deportivas de OSM Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Censo Nacional de Mercados de Abastos 2016 del INEI](https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1448/libro.pdf)
''')

st.write('''
*La localización de los mercados itinerantes inicialmente se recomiendó en zonas alejadas debido a 
la falta de accesibilidad pero debido a ciertas limitaciones logística de la municipalidad se filtraron 
los parques en zonas poco accesibles.
''')

st.subheader('Autores')
st.write('''
Andrés Regal  
Claudio Ortega  
Universidad del Pacífco
''')

