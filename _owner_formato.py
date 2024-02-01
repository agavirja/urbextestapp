import streamlit as st
import pandas as pd
import numpy as np
import shapely.wkt as wkt
import plotly.express as px
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from bs4 import BeautifulSoup

from modulos.display_owner_map import display_owner_map
from scripts.getpropertiesbyID import getpropertiesbyID

from modulos.stylefunctions import style_function,style_referencia,style_lote_transacciones,style_lote

def main(inputvar):

    formato = {
               'reporte_owner':False,
               'owner_inputvar':None
               }
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value

    col1,col2,col3 = st.columns(3)
    with col3:
        if st.button('Nueva busqueda'):
            st.session_state.reporte_owner = False
            st.session_state.owner_inputvar = {}
            st.rerun()
            
    data,dataprocesos = getpropertiesbyID(inputvar)
    latitud  = 4.687489
    longitud = -74.056424 
    display_owner_map(data[data['wkt'].notnull()],latitud,longitud)