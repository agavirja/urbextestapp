import streamlit as st
import pandas as pd
from sqlalchemy import create_engine 

from scripts.formato_direccion import formato_direccion
from scripts.getuso_destino import getuso_destino
from scripts.groupcatastro import groupcatastro

@st.cache_data
def getdatamarket(polygon=None, tipoinmueble=None, tiponegocio=None, areamin=0, areamax=0, valormin=0, valormax=0, habitacionesmin=0, habitacionesmax=0, banosmin=0, banosmax=0, garajesmin=0, garajesmax=0):
    
    datamarket = pd.DataFrame()
    if tipoinmueble is not None and tiponegocio is not None:
        user        = st.secrets["user_bigdata"]
        password    = st.secrets["password_bigdata"]
        host        = st.secrets["host_bigdata_lectura"]
        schema      = 'market'
        engine      = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    
        if 'venta' in tiponegocio.lower():
            variable = 'valorventa'
        elif 'arriendo' in tiponegocio.lower():
            variable = 'valorarriendo'
            
        query = ''
        if areamin > 0:
            query += f" AND areaconstruida >= {areamin}"
        if areamax > 0:
            query += f" AND areaconstruida <= {areamax}"
        if valormin > 0:
            query += f" AND {variable} >= {valormin}"
        if valormax > 0:
            query += f" AND {variable} <= {valormax}"
        if habitacionesmin > 0:
            query += f" AND habitaciones >= {habitacionesmin}"
        if habitacionesmax > 0:
            query += f" AND habitaciones <= {habitacionesmax}"
        if banosmin > 0:
            query += f" AND banos >= {banosmin}"
        if banosmax > 0:
            query += f" AND banos <= {banosmax}"
        if garajesmin > 0:
            query += f" AND garajes >= {garajesmin}"
        if garajesmax > 0:
            query += f" AND garajes <= {garajesmax}"

        if query!='':
            query = query.strip().strip('AND').strip()
            query = query+' AND ' 
        
        addvar  = ''
        addlist = []
        if any([x for x in ['apartamento','casa'] if x in tipoinmueble.lower()]):
            addvar  = 'habitaciones,banos,'
            addlist = ['habitaciones','banos','garajes']
            
        tabla = f'data_ofertas_{tiponegocio.lower()}_{tipoinmueble.lower()}_bogota'
        datamarket = pd.read_sql_query(f"SELECT code,tiponegocio,tipoinmueble,direccion,fecha_inicial,antiguedad,areaconstruida,valorventa,valorarriendo,valormt2,{addvar}garajes,estrato,scanombre,inmobiliaria,latitud,longitud, img1 as imagen_principal FROM  {schema}.{tabla} WHERE {query} ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'), geometry)" , engine)
        engine.dispose()

        if not datamarket.empty:
            listadrop  = addlist+[variable,'areaconstruida'] # 'direccion'
            datamarket = datamarket.sort_values(by='fecha_inicial',ascending=False)
            datamarket = datamarket.drop_duplicates(subset=listadrop,keep='first')
            
    return datamarket


@st.cache_data
def getdatamarketbycode(code=None, tipoinmueble=None, tiponegocio=None):
    
    datamarket = pd.DataFrame()
    if code is not None and tipoinmueble is not None and tiponegocio is not None:
        user        = st.secrets["user_bigdata"]
        password    = st.secrets["password_bigdata"]
        host        = st.secrets["host_bigdata_lectura"]
        schema      = 'market'
        engine      = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
                
        tabla      = f'data_ofertas_{tiponegocio.lower()}_{tipoinmueble.lower()}_bogota'
        datamarket = pd.read_sql_query(f"SELECT * FROM  {schema}.{tabla} WHERE code='{code}'" , engine)
        engine.dispose()

    return datamarket

@st.cache_data
def getdatamarketbycoddir(coddir=None, tipoinmueble=None, tiponegocio=None):
    
    datamarket = pd.DataFrame()
    if coddir is not None and tipoinmueble is not None and tiponegocio is not None:
        user       = st.secrets["user_bigdata"]
        password   = st.secrets["password_bigdata"]
        host       = st.secrets["host_bigdata_lectura"]
        schema     = 'market'
        engine     = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')

        addvar  = ''
        if any([x for x in ['apartamento','casa'] if x in tipoinmueble.lower()]):
            addvar  = 'habitaciones,banos,'
                    
        tabla      = f'data_ofertas_{tiponegocio.lower()}_{tipoinmueble.lower()}_bogota'
        datamarket = pd.read_sql_query(f"SELECT code,tiponegocio,tipoinmueble,direccion,fecha_inicial,areaconstruida,valorventa,valorarriendo,valormt2,{addvar}garajes,inmobiliaria,latitud,longitud, imagen_principal FROM  {schema}.{tabla} WHERE coddir='{coddir}'" , engine)
        engine.dispose()

    return datamarket
