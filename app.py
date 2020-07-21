import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

@st.cache
def read_geojson(fp):
    gdf = gpd.read_file(fp, driver='GeoJSON')
    return gdf

up_logo = Image.open('images/inge-logo.png')
st.image(up_logo, width=200, format='png')

st.title('Análisis de ubicación de mercados itinerantes')

# Problema de aglomeracion de personas en el mercado, solucion viable es colocas mas mercados (itinerates)
st.write('''
Desde el inicio del Estado de Emergencia en nuestro país los mercados han recibido un gran volumen de personas.
Esto ha generado que se conviertan en uno de los principales focos de contagio de COVID-19 para la población. Por este motivo
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
En ese sentido para facilitar el análisis de estas variables hemos divido la ciudad en hexágonos de ~0.73km$^2
$. Por ejemplo en el mapa de Lima mostrado a continuación podemos ver cuántos minutos se demoraría una persona
caminando desde el centro de un hexágono hasta el mercado más cercano. Mientras más oscuro sea el color del
hexágono significa existe un menor acceso a mercados en esa zona.
''')

lima_hexs = read_geojson('inputs/lima_hexs.geojson')

fig_durations = px.choropleth_mapbox(
    lima_hexs.reset_index(), geojson=lima_hexs.geometry.__geo_interface__, locations='index',
    color='duration_to_food_facility_bins',
    color_discrete_sequence=px.colors.sequential.Plasma_r,
    category_orders={'duration_to_food_facility_bins': ['De 0 a 15', 'De 15 a 30', 'De 30 a 45', 'De 45 a 60', 'De 60 a 90', 'De 90 a 120', 'Más de 120']},
    mapbox_style="carto-positron",
    zoom=9,
    center = {
       "lat": lima_hexs.geometry.unary_union.centroid.y,
       "lon": lima_hexs.geometry.unary_union.centroid.x
    },
    opacity=0.3,
    labels={
        'duration_to_food_facility_bins': 'Duración (en minutos)',
        'duration_to_food_facility': 'Duración',
        'distance_to_food_facility': 'Distancia',
        'n_markets': '# de mercados'
    },
    hover_data = ['duration_to_food_facility', 'distance_to_food_facility', 'n_markets']
)
fig_durations.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig_durations.update_traces(marker=dict(line=dict(width=0)))
st.plotly_chart(fig_durations, use_container_width=True)

st.write('''
Además, **la cantidad de mercados** ubicados en una zona geográfica **debería ser acorde a la densidad poblacional.**
Asimismo, **el flujo de personas** en el mercado debe estar **restringido por el aforo** para
que sea posible **mantener la distancia social.** En el mapa de abajo podemos ver la cantidad de personas
por hexágono en la ciudad de Lima y si pasamos nuestro cursor por encima de un hexágono podemos ver el número de mercados dentro:
''')

fig_population = px.choropleth_mapbox(
    lima_hexs.reset_index(), geojson=lima_hexs.geometry.__geo_interface__, locations='index',
    color='population_2020',
    color_continuous_scale='viridis',
    mapbox_style="carto-positron",
    zoom=9,
    center = {
       "lat": lima_hexs.geometry.unary_union.centroid.y,
       "lon": lima_hexs.geometry.unary_union.centroid.x
    },
    opacity=0.3,
    labels={
        'population_2020': 'Población',
        'n_markets': '# de mercados'
    },
    hover_data = ['n_markets']
)
fig_population.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig_population.update_traces(marker=dict(line=dict(width=0)))
st.plotly_chart(fig_population, use_container_width=True)

# Para solucionar este problema de ubicación se ha usado un Modelo de localización óptima instalaciones
st.write('''
Por otro lado **los datos de flujos de personas se podrían obtener a partir de fuentes privadas como empresas
de telecomunicaciones o específicamente Google**. Sin embargo aún no tenemos acceso esa información.
''')

# 0. se aplicó la primera prueba para distritios adebido a que cada municipalidad dsitrital tiene la facultad de implementar los mercaods itinerantes
st.subheader('Propuesta de solución')
st.write('''
Para resolver la pregunta de dónde es la ubicación óptima para los mercados **contamos con la
densidad poblacional y la duracion del viaje**. Asi pues, podemos recurrir a modelos de optimización utilizados en el
área de la logística. Uno de ellos es **el modelo de optimización de localización de instalaciones** (FLP, por sus siglas
en inglés) permite minimizar los costos de transporte al tiempo que considera factores como la demanda. En este caso
**vamos a minizar la distancia recorrida por las personas hacia los mercados considerando que la cantidad de personas
que asistan a cada mercado no sobrepase su aforo.**
''')

st.subheader('Resultados ')
st.write('''
En el siguiente mapa podrás visualizar las ubicaciones seleccionadas de los mercados potenciales y
la ubicación de los mercados actuales.
''')

# Lee los datos para el mapa
lima_distritos = read_geojson('inputs/lima_distritos.geojson')
market_db = read_geojson('inputs/market_db.geojson')
active_temporal_markets_poly = read_geojson('inputs/active_temporal_markets_poly.geojson')

st.subheader("Mapa de mercados")

# Filtra el distrito
options = ['Todos'] + sorted(lima_distritos['distrito'].unique().tolist())
option = st.selectbox('Selecciona el distrito que deseas ver', options)

if option == 'Todos':
    selected_district = lima_distritos
    selected_market = market_db
    selected_temp_market = active_temporal_markets_poly
    zoom_level = 10
else:
    selected_district = lima_distritos[lima_distritos['distrito'] == option]
    selected_market = market_db[market_db['distrito'] == option]
    selected_temp_market = active_temporal_markets_poly[active_temporal_markets_poly['distrito'] == option]
    zoom_level = 12

# Mapa
fig = go.Figure()

fig.add_trace(
    go.Choroplethmapbox(
        name='Distritos',
        customdata=selected_district['distrito'],
        geojson=selected_district.geometry.__geo_interface__,
        locations=selected_district.index,
        z=selected_district['z'],
        marker_line_width=1,
        marker_line_color='rgba(0,0,0,0.5)',
        colorscale=[[0, 'rgba(255,255,255,0)'], [1,'rgba(255,255,255,0)']],
        hovertemplate='Distrito:%{customdata}',
        hoverlabel_namelength = 0,
        showscale=False,
    )
)

fig.add_trace(
    go.Scattermapbox(
        name='Mercados',
        customdata=selected_market[['NOMBRE_MERCADO', 'aforo']],
        lat=selected_market.latitude,
        lon=selected_market.longitude,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=selected_market['aforo_scaled'],
            sizemin=10,
            color='orange',
            opacity=0.5,
        ),
        line={'color': 'black', 'width':50},
        hovertemplate='Nombre:%{customdata[0]} <br><b>Aforo:%{customdata[1]} ',
        showlegend=True,
    )
)

fig.add_trace(
    go.Choroplethmapbox(
        name='Potenciales mercados itinerantes',
        customdata=selected_temp_market[['display_address', 'aforo']],
        geojson=selected_temp_market.geometry.__geo_interface__,
        locations=selected_temp_market.index, z=selected_temp_market.is_active,
        colorscale=[[0, 'rgb(0,255,0)'], [1,'rgb(0,255,0)']],
        showscale=False,
        showlegend=True,
        marker_opacity=0.5, marker_line_width=3, marker_line_color='rgb(0,200,0)',
        hovertemplate='Dirección:%{customdata[0]} <br><b>Aforo:%{customdata[1]:.0f} ',
        hoverlabel_namelength = 0
    )
)

fig.update_layout(
    legend={'orientation': 'h'},
    mapbox=dict(
        center=dict(
            lat=selected_district.geometry.unary_union.centroid.y,
            lon=selected_district.geometry.unary_union.centroid.x
        ),
        pitch=0,
        zoom=11,
        style='carto-positron'
    ),
    margin={"r":0,"t":0,"l":0,"b":0}
)

st.plotly_chart(fig, use_container_width=True)

# df las direcciones
address_df = active_temporal_markets_poly[['lat', 'lon', 'display_address']]
if st.checkbox('Muestra los datos de los potenciales mercados'):
    st.subheader('Ubicación de potenciales mercados itinerantes ')
    st.write(address_df)

# Discusión
st.write('''
Este mapa puede ser utilizado y evaluado por autoridades municipales para ayudarlos a
seleccionar estratégicamente la mejor ubicación de los mercados itinerantes en su distrito.
Si tomamos el distrito de **San Juan de Lurigancho** como ejemplo, se puede observar que **se ha recomendado colocar
un gran número de mercados itinerantes en la zona central del distrito debido a la alta concentración de personas.**
Asimismo, **se recomendó colocar mercados itinerantes en zonas de limitado acceso vial**, para facilitar
el acceso a mercados de los vecinos.
''')

# Discusión
st.write('''
También es importante mencionar que estos resultados pueden mejorarse con acceso a datos de movilidad de personas
y la aplicación de un mayor número de restricciones al modelo de optmización para lograr **describir mejor la realidad**.
Por otro lado, es importantísimo el trabajo de **comunicación y concientización de la población** para que se logren los
resultados esperados.''')

# 2. Preprocesaminto: Formato a los datos para el modelo

st.subheader('¿Cómo logramos estos resultados?')
st.write('''
Primero, se descargaron los límites de la ciudad y se dividió el espacio geográfico en hexágonos de ~0.73km$^2$ (como se mencionó
anteriormente para los mapas). Luego se obtuvieron
los datos poblacionales en una resolución de 30x30m, estos datos los usamos como un estimado de la cantidad de clientes.
Después mediante la ubicación de los parques y losas deportivas de cada distrito, construimos nuestro conjunto de
mercados itinerantes potenciales. Asimismo, sólo se consideraron parques y losas con un área que permita tener un aforo
 de 500 personas considerando el distanciamiento social necesario. Utilizando tanto los mercados actuales, mercados potenciales y los hexágonos se contruyó
una **matriz de distancia** que nos indica cuánto se demora una persona caminando para movilizarse de cualquier hexágono
a cualquier mercado.

Con respecto al aforo de los mercados debido que no está reportado en el censo, lo tuvimos que estimar a partir del
área construida de cada mercado. Este valor sirve para restringir la cantidad de personas que pueden ser
asignadas a un mercado. Por otro lado **el modelo necesita que le digamos el número total de mercados
itinerantes que se activarán**, para ello la Municipalidad nos indicó que la capacidad logística de los distritos en promedio
podría alcanzar para implementar **~12 mercados itinerantes** en un mes, lo que nos da un total de 516 mercados itinerantes para
toda la ciudad.

En resumen se han calculado las siguientes variables que el modelo necesita:

- Matriz de distancia mercado-clientes (filas-columnas)
- Aforo de cada mercado
- Número de instalaciones a activar (según la capacidad logística de cada distrito)
''')

# 3. Procesamiento: que hace el modelo ? minimizar la distacia crespentadfo lazs restrs.
# que podria salir mal? consideraciones

st.write('''
Una vez concluida la optimización el modelo retorna dos resultados:
- La ubicación de los nuevos mercados itinerantes que se deben implementar
- La población que debe ser atendida por los mercados (restringido por el aforo)

Estos fueron utilizados para realizar el mapa mostrado anteriormente. Como conclusión
podríamos decir el uso de datos abiertos, técnicas de analisis y visualizacion de datos geoespaciales
pueden y deben ser herramientas que faciliten el trabajo de los servidores públicos, para mejorar
la calidad de vida de los ciudadanos.
''')

st.subheader('¿Qué podemos mejorar?')
st.write('''
Desde el punto de vista técnico podemos mejorar varios aspectos, algunos serían:

- Automatizar la selección de potenciales mercados itinerantes según las recomendaciones de los tomadores de decisión (área, acceso vial, entre otros)
- Reportar métricas de accesibilidad.
- Obtener datos de movilidad de personas.

Asimismo, la retroalimentación y sugerencias de los usuarios serán de gran ayuda
para que la herramienta sea de la mayor utilidad posible.
''')

# TODO: % De gente asignado a cada instalacion ()
# TODO: Distancia y duracion (comparacion de escenarios)


# 1. Fuente de datos: Urbapy(Pobalcion HDX FB, Limites OSM, Censo de Mercados INEI, POIS de Overpas OSM)
st.subheader('Fuentes de datos')
st.write('''
Se utilizaron las siguientes fuentes de datos:

- [Peru: High Resolution Population Density Maps + Demographic Estimates](https://data.humdata.org/dataset/peru-high-resolution-population-density-maps-demographic-estimates)
- [Límites políticos del Servicio Nominatim de Open Street Maps (OSM)](https://nominatim.openstreetmap.org/)
- [Geolocalización de parques y losas deportivas de OSM Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Censo Nacional de Mercados de Abastos 2016 del INEI](https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1448/libro.pdf)
''')

st.subheader('Autores')
st.write('''
Andrés Regal, Claudio Ortega & Michelle Rodríguez\n
Facultad de Ingeniería\n
Universidad del Pacífico
''')
