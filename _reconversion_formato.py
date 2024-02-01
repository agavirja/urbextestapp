import streamlit as st
import pandas as pd
import numpy as np
import shapely.wkt as wkt
import plotly.express as px
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from bs4 import BeautifulSoup

from scripts.getdatabarmanpre import getdatabarmanpre
from modulos.display_reconversion_map import display_reconversion_map

def main(inputvar):
    
    formato = {
               'reporte_reconversion':False,
               'inputvar_reconversion':{}
               }
    
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
            
    col1,col2,col3 = st.columns(3)
    with col3:
        if st.button('Nueva busqueda'):
            st.session_state.reporte_reconversion = False
            st.session_state.inputvar_reconversion = {}
            st.rerun()
 
    data, datalotes = getdatabarmanpre(inputvar)
    latitud  = 4.687489
    longitud = -74.056424 
    display_reconversion_map(datalotes[(datalotes['latitud'].notnull()) & (datalotes['longitud'].notnull())],latitud,longitud)
    