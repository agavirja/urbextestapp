import streamlit as st
import pandas as pd
import numpy as np
import shapely.wkt as wkt
import plotly.express as px
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from bs4 import BeautifulSoup

from scripts.getdataBrands import getdatabrans


from modulos.display_brand_map import display_brand_map


def main(inputvar):

    formato = {
               'reporte_mapeo_marcas':False,
               'inputvar_mapeo_marcas':None
               }
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value

    col1,col2,col3 = st.columns(3)
    with col3:
        if st.button('Nueva busqueda'):
            st.session_state.reporte_mapeo_marcas = False
            st.session_state.inputvar_mapeo_marcas = {}
            st.rerun()
                
    data     = getdatabrans(inputvar)
    latitud  = 4.687489
    longitud = -74.056424 
    data     = data[(data['latitud'].notnull()) & (data['longitud'].notnull())]
    
    if not data.empty:
        label = data['label'].iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        
        options    = list(data['empresa'].unique())
        isdisabled = True
        if len(options)>1:
            options    = ['Todas'] + options
            isdisabled = False

        with col1:
            empresa = st.selectbox('Filtro por marca', options=options, disabled=isdisabled)
            if 'Todas' not in empresa:
                data = data[data['empresa']==empresa]
            
        with col2:
            options = ['Todas']+list(data[data['nombre'].notnull()]['nombre'].unique())
            nombre = st.selectbox(f'{label}', options=options)
            if 'Todas' not in nombre:
                data = data[data['nombre']==nombre]
                
        with col3:
            options = ['Todos']+list(data[data['prenbarrio'].notnull()]['prenbarrio'].unique())
            barrio = st.selectbox('Barrio', options=options)
            if 'Todos' not in barrio:
                data = data[data['prenbarrio']==barrio]
                
        with col4:
            options   = list(data[data['direccion'].notnull()]['direccion'].unique())+ list(data[data['predirecc'].notnull()]['predirecc'].unique())
            options   = ['Todas']+options
            direccion = st.selectbox('Dirección', options=options)
            if 'Todas' not in direccion:
                idd  = (data['direccion']==direccion) | (data['predirecc']==direccion)
                data = data[idd]
                
        with col5:
            id_trans = st.selectbox('Transacciones', options=['Todo','Si'])
            if 'Si' in id_trans:
                data = data[data['fuente']=='snr']
                     
    display_brand_map(data,latitud,longitud)

    if not data.empty:
        col1, col2 = st.columns(2)
        with col1:
            df         = data.groupby('empresa').agg({'label':'count','marker':'first','marker_color':'first'}).reset_index()
            df.columns = ['empresa','conteo','marker','marker_color']
            df         = df.sort_values(by='conteo',ascending=False)
            df.index   = range(len(df))
            fig        = px.bar(df, x="conteo", y="empresa", orientation='h',color="empresa")
            st.plotly_chart(fig, use_container_width=True)
        