import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from sqlalchemy import create_engine 

from _mapeo_marcas_formato import main as reporte

from scripts.getdataBrands import getoptions

def main():
    formato = {
               'reporte_mapeo_marcas':False,
               'inputvar_mapeo_marcas':None
               }
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value

    if st.session_state.reporte_mapeo_marcas is False:
        col1,col2 = st.columns(2)
        dataoptions   = getoptions()
        with col1:
            seleccion = st.selectbox('Selección por tipo:', options=sorted(list(dataoptions['label'].unique())))
        
        with col2:
            st.image('https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/imagenes_app/commercial_building.png')


        try:    idxlabel = dataoptions[dataoptions['label']==seleccion]['idxlabel'].iloc[0]
        except: idxlabel = None
        
        st.session_state.inputvar_mapeo_marcas = {'mpio_ccdgo':'11001', 'label':seleccion,'idxlabel':idxlabel}
        with col1:
            st.write('')
            st.write('')
            if st.button('Buscar'):
                st.session_state.reporte_mapeo_marcas = True
                st.rerun()
                
    if st.session_state.reporte_mapeo_marcas:
        with st.spinner('Buscando información'):
            reporte(st.session_state.inputvar_mapeo_marcas)

    components.html(
        """
    <script>
    const elements = window.parent.document.querySelectorAll('.stButton button')
    elements[0].style.backgroundColor = '#68c8ed';
    elements[0].style.fontWeight = 'bold';
    elements[0].style.color = 'white';
    elements[0].style.width = '100%';
    elements[1].style.backgroundColor = '#68c8ed';
    elements[1].style.fontWeight = 'bold';
    elements[1].style.color = 'white';
    elements[1].style.width = '100%';
    </script>
    """
    )