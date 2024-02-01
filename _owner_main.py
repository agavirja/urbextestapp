import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from sqlalchemy import create_engine 

from _owner_formato import main as reporte

def main():
    formato = {
               'reporte_owner':False,
               'owner_inputvar':None
               }
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
                
    if st.session_state.reporte_owner is False:
        col1,col2 = st.columns(2)
        with col1:
            tipodocumento  = st.selectbox('Tipo de documento',options=['','C.C.', 'N.I.T.', 'C.E.', 'PASAPORTE', 'T.I.'])
        with col1:
            if tipodocumento!='':
                identificacion = st.text_input('Número de documento',value='')
            else:
                identificacion = st.text_input('Número de documento',value='',disabled=True)
        with col1:
            titular        = st.text_input('Nombre del titular',value='')

        with col2:
            st.image('https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/imagenes_app/commercial_building.png')

        st.session_state.owner_inputvar = {'tipodocumento':tipodocumento, 'identificacion':identificacion,'titular':titular}
        with col1:
            st.write('')
            st.write('')
            if st.button('Buscar'):
                st.session_state.reporte_owner = True
                st.rerun()
                
    if st.session_state.reporte_owner:
        with st.spinner('Buscando información'):
            reporte(st.session_state.owner_inputvar)

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