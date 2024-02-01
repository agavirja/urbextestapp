import streamlit as st

from _duedilligence_main import main

st.set_page_config(layout="wide",initial_sidebar_state="auto")

formato = {
           'code':None,
           'variable':None,
           }

for key,value in formato.items():
    if key not in st.session_state: 
        st.session_state[key] = value
 
# obtener los argumentos de la url
args = st.experimental_get_query_params()
if 'code' in args: 
    st.session_state.code = args['code'][0]
if 'variable' in args:
    st.session_state.variable = args['variable'][0]

inputvar = None
if st.session_state.variable=='chip':
    inputvar = {'chip':st.session_state.code,'matricula':'','direccion':'','barmanpre':'','metros':500}
elif st.session_state.variable=='barmanpre':
    inputvar = {'chip':'','matricula':'','direccion':'','barmanpre':st.session_state.code,'metros':500}
elif st.session_state.variable=='direccion':
    inputvar = {'chip':'','matricula':'','direccion':st.session_state.variable,'barmanpre':'','metros':500}
elif st.session_state.variable=='matricula':
    inputvar = {'chip':'','matricula':st.session_state.variable,'direccion':'','barmanpre':'','metros':500}

main(inputvar)