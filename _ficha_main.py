import streamlit as st
from _ficha_formato import main as reporte

def main(inputvar):
    
    formato = {
               'code':None,
               'tiponegocio':None,
               'tipoinmueble':None,
               'ficha_inputvar':inputvar
               }

    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
            
    code         = inputvar['code'] if 'code' in inputvar else None
    tipoinmueble = inputvar['tipoinmueble'] if 'tipoinmueble' in inputvar else None
    tiponegocio  = inputvar['tiponegocio'] if 'tiponegocio' in inputvar else None
    
    if code is not None and tipoinmueble is not None and tiponegocio is not None:
        reporte(code,tipoinmueble,tiponegocio)
    else:
        st.session_state.code           = st.text_input('Código',value=code)
        st.session_state.tipoinmueble   = st.selectbox('Tipo de inmueble',options=['Apartamento','Casa',''])
        st.session_state.tiponegocio    = st.selectbox('Tipo de Negocio',options=['Venta','Arriendo',''])
        st.session_state.ficha_inputvar = {'code':st.session_state.code,'tiponegocio':st.session_state.tiponegocio,'tipoinmueble':st.session_state.tipoinmueble}
        st.experimental_rerun()
