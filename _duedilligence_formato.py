import streamlit as st
import pandas as pd
import numpy as np
import shapely.wkt as wkt
import plotly.express as px
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from bs4 import BeautifulSoup

from scripts.inmuebleANDusosuelo import usosuelo2inmueble
from scripts.getinfopredial import getinfopredial
from scripts.getdatamarketcoddir import getdatamarketcoddir
from scripts.getrango import getrango

from modulos.stylefunctions import style_function,style_lote,style_lote_transacciones,style_referencia
from modulos.display_datamarket import display_datamarket
from modulos.map_streetview import map_streetview
from modulos.display_descripcion_predio import display_descripcion_predio
from modulos.display_shd import display_shd
from modulos.display_snr_proceso import display_snr_proceso
from modulos.display_predios_lote import display_predios_lote
from modulos.display_transacciones_polygon import display_transacciones_polygon
from modulos.display_dane import display_dane

def main(inputvar):
    
    formato = {
               'reporte_duedilligence':False,
               'inputvar_duedilligence':{}
               }
    for key,value in formato.items():
        if key not in st.session_state: 
            st.session_state[key] = value
                
    col1,col2,col3 = st.columns(3)
    with col3:
        if st.button('Nueva busqueda'):
            st.session_state.reporte_duedilligence = False
            st.session_state.inputvar_duedilligence = {}
            st.rerun()
                    
    dataparticular_catastro,datageneral_catastro,datalote_particular,datalotespolygon,datacatastropolygon,datavigencia_particular,datavigencia_general,datasnrprocesos,datasnrtable,polygonfilter,latitud,longitud,usosuelo = getinfopredial(inputvar)

    if dataparticular_catastro.empty and datageneral_catastro.empty and datacatastropolygon.empty:
        desc_predio = ""
        if 'chip' in inputvar and inputvar['chip']:
            desc_predio = f" para el chip {inputvar['chip']}"
        elif 'direccion' in inputvar and inputvar['direccion']: 
            desc_predio = f" para la dirección {inputvar['direccion']}"
        elif 'matricula' in inputvar and inputvar['matricula']:  
            desc_predio = f" para la matrícula {inputvar['matricula']}"
        elif 'nombrepropiedad' in inputvar and inputvar['nombrepropiedad']:  
            desc_predio = f" para el nombre de la propiedad {inputvar['nombrepropiedad']}"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
          <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
        </head>
        <body>
        <div class="container-fluid py-1" style="margin-top: 0px;margin-bottom: 50px;">
          <div class="row">
            <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
              <div class="card">
                <div class="card-body p-3">
                  <div class="row">
                    <div class="numbers">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">No se encontró información del predio {desc_predio}</h3>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </body>
        </html>        
        """
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(texto, unsafe_allow_html=True)

    #-------------------------------------------------------------------------#
    # Mapa y streetview
    #-------------------------------------------------------------------------#
    polygon = None
    if not datalote_particular.empty:
        polygon = wkt.loads(datalote_particular['wkt'].iloc[0]) 
        map_streetview(polygon)
        
    if not latitud and not longitud and polygon:
        try:
            polygonl = wkt.loads(polygon) 
            latitud  = polygonl.centroid.y
            longitud = polygonl.centroid.x
        except: 
            try:
                latitud  = polygon.centroid.y
                longitud = polygon.centroid.x
            except: pass
        
    if latitud and longitud and not polygon:
        map_streetview(polygon=None,latitud=latitud,longitud=longitud)
            
    #-------------------------------------------------------------------------#
    # Descripcion del predio/Edificio
    #-------------------------------------------------------------------------#
    display_descripcion_predio(dataparticular_catastro,datageneral_catastro)

    #-------------------------------------------------------------------------#
    # Descripcion SHD del predio
    #-------------------------------------------------------------------------#
    display_shd(datavigencia_particular,titulo='Histórico catastral del predio')


    #-------------------------------------------------------------------------#
    # Descripcion SNR del predio
    #-------------------------------------------------------------------------#
    dataprocesos_particular = pd.DataFrame()
    if not datasnrprocesos.empty and not datasnrtable.empty and not dataparticular_catastro.empty:
        idd = datasnrtable['prechip']==dataparticular_catastro['prechip'].iloc[0]
        if sum(idd)>0:
            idd = datasnrprocesos['docid'].isin(datasnrtable[idd]['docid'])
            dataprocesos_particular = datasnrprocesos[idd]
        
    display_snr_proceso(dataprocesos_particular,titulo='Transacciones del predio')


    #-------------------------------------------------------------------------#
    # Descripcion de los predios del edificio
    #-------------------------------------------------------------------------#
    if not datageneral_catastro.empty and len(datageneral_catastro)>1:
        title = ""
        if not dataprocesos_particular.empty:
            tipo = ' del lote'
            if datageneral_catastro['preaconst'].sum()>0: tipo = ' del edificio / construcción'
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
              <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
            </head>
            <body>
            <div class="container-fluid py-1" style="margin-top: 0px;margin-bottom: 0px;">
              <div class="row">
                <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
                  <div class="card">
                    <div class="card-body p-3">
                      <div class="row">
                        <div class="numbers">
                          <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">Información {tipo}</h3>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </body>
            </html>        
            """
            texto = BeautifulSoup(html, 'html.parser')
            st.markdown(texto, unsafe_allow_html=True)
        else:
            title = """
            <div class="container-fluid py-4">
              <div class="row" style="margin-bottom: 0px;margin-top: -40px;">
                <div class="card-body p-3">
                  <div class="row">
                    <div class="numbers">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center; font-size: 1.5rem; padding-bottom: 8px;">Transacciones del edificio </h3>
                    </div>
                  </div>
                </div>
              </div>
            </div>    
            """
        #---------------------------------------------------------------------#
        # Composicion de los predios
        col1, col2 = st.columns(2)
        with col1:
            df         = datageneral_catastro.groupby('usosuelo')['prechip'].count().reset_index()
            df.columns = ['usosuelo','predios']
            df         = df.sort_values(by='predios',ascending=False)
            df.index   = range(len(df))
            fig        = px.bar(df, x="usosuelo", y="predios", text="predios", title="Tipología de predios")
            fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
            fig.update_layout(title_x=0.5,height=400, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
  
        with col2:
            df = datageneral_catastro[datageneral_catastro['preaconst'].notnull()]
            df = getrango(df,'preaconst')
            df['conteo'] = 1
            df = df.groupby(['rango','categoria'])['conteo'].count().reset_index()
            df.columns   = ['rango','categoria','conteo']
            df           = df[df['conteo']>0]
            df           = df.sort_values(by='categoria',ascending=True)
            df.index     = range(len(df))
            fig          = px.bar(df, x="rango", y="conteo", text="conteo", title="Área construida")
            fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
            fig.update_layout(title_x=0.5,height=400, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")

        #---------------------------------------------------------------------#
        # Descripcion predios en el edificio
        display_predios_lote(datageneral_catastro,titulo='Descripción de predios')

        #---------------------------------------------------------------------#
        # Transacciones en el edificio
        dataprocesos_lote = pd.DataFrame()
        if not datasnrtable.empty:
            idd = datasnrtable['prechip'].isin(datageneral_catastro['prechip'])
            if sum(idd)>0:
                idd = datasnrprocesos['docid'].isin(datasnrtable[idd]['docid'])
                if sum(idd)>0:
                    dataprocesos_lote = datasnrprocesos[idd]
                    idd               = dataprocesos_lote['codigo'].isin(['125','126','168','169','0125','0126','0168','0169'])
                    dataprocesos_lote = dataprocesos_lote[idd]
        
        display_snr_proceso(dataprocesos_lote,titulo='Transacciones en el mismo edificio',downloadname='Descargar  información',showstats=True)

        #---------------------------------------------------------------------#
        # Analisis de las transacciones
        if not dataprocesos_lote.empty:
            col1, col2 = st.columns(2)
            with col1:
                df = dataprocesos_lote[dataprocesos_lote['preaconst'].notnull()]
                df = getrango(df,'preaconst')
                df['conteo'] = 1
                df = df.groupby(['rango','categoria'])['conteo'].count().reset_index()
                df.columns   = ['rango','categoria','conteo']
                df           = df[df['conteo']>0]
                df           = df.sort_values(by='categoria',ascending=True)
                df.index     = range(len(df))
                fig          = px.bar(df, x="rango", y="conteo", text="conteo", title="Áreas de los predios de transacciones")
                fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                
            with col2:
                df = dataprocesos_lote[dataprocesos_lote['preaconst'].notnull()]
                df = df[(df['cuantia']>0) & (df['preaconst']>0)]
                df['cuantia'] = df['cuantia']/df['preaconst']
                df            = getrango(df,'preaconst')
                df['conteo']  = 1
                df = df.groupby(['rango','categoria'])['cuantia'].median().reset_index()
                df.columns   = ['rango','categoria','cuantia']
                df           = df[df['cuantia']>0]
                df           = df.sort_values(by='categoria',ascending=True)
                df.index     = range(len(df))
                fig          = px.bar(df, x="rango", y="cuantia", text="cuantia", title="Cuantía por área de los predios")
                fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                
            with col1:
                df = dataprocesos_lote.groupby('year')['cuantia'].count().reset_index()
                df.columns  = ['year','conteo']
                df['year']   = pd.to_numeric(df['year'],errors='coerce')
                df           = df[(df['conteo']>0) & (df['year']>0)]
                df           = df.sort_values(by='year',ascending=True)
                df.index     = range(len(df))
                df['year']   = df['year'].astype(int).astype(str)
                fig          = px.bar(df, x="year", y="conteo", text="conteo", title="Transacciones por año")
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                
            with col2:
                df = dataprocesos_lote[dataprocesos_lote['cuantia'].notnull()]
                df = getrango(df,'cuantia')
                df['conteo'] = 1
                df = df.groupby(['rango','categoria'])['conteo'].count().reset_index()
                df.columns   = ['rango','categoria','conteo']
                df           = df[df['conteo']>0]
                df           = df.sort_values(by='categoria',ascending=True)
                df.index     = range(len(df))
                try: df['rango'] = df['rango'].apply(lambda x: f"${x:,.0f} MM")
                except: pass
                fig          = px.bar(df, x="rango", y="conteo", text="conteo", title="Transacciones por cuantía")
                fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")

    #-------------------------------------------------------------------------#
    # Informacion del radio
    #-------------------------------------------------------------------------#
    if not datalotespolygon.empty:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
          <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
        </head>
        <body>
        <div class="container-fluid py-1" style="margin-top: -20px;margin-bottom: 0px;">
          <div class="row">
            <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
              <div class="card">
                <div class="card-body p-3">
                  <div class="row">
                    <div class="numbers">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">Transacciones en un radio de {inputvar['metros']} metros</h3>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </body>
        </html>        
        """
        texto = BeautifulSoup(html, 'html.parser')
        st.markdown(texto, unsafe_allow_html=True)
            
        barmanpreref = None
        if not datageneral_catastro.empty:
            barmanpreref = datageneral_catastro['barmanpre'].iloc[0]
            
            
        #---------------------------------------------------------------------#
        # Mapa de transacciones en el radio
        dataprocesos_radio = pd.DataFrame()
        if not datasnrtable.empty and not datacatastropolygon.empty:
            idd = datasnrtable['prechip'].isin(datacatastropolygon['prechip'])
            if sum(idd)>0:
                idd = datasnrprocesos['docid'].isin(datasnrtable[idd]['docid'])
                if sum(idd)>0:
                    dataprocesos_radio = datasnrprocesos[idd]
                    idd                = dataprocesos_radio['codigo'].isin(['125','126','168','169','0125','0126','0168','0169'])
                    dataprocesos_radio = dataprocesos_radio[idd]
        
        display_transacciones_polygon(dataprocesos_radio,datalotespolygon,polygon=polygonfilter,latitud=latitud,longitud=longitud,barmanpreref=barmanpreref)
    
        #---------------------------------------------------------------------#
        # Analisis de las transacciones
        if not dataprocesos_radio.empty:
            col1, col2 = st.columns(2)
            with col1:
                df = dataprocesos_radio[dataprocesos_radio['preaconst'].notnull()]
                df = getrango(df,'preaconst')
                df['conteo'] = 1
                df = df.groupby(['rango','categoria'])['conteo'].count().reset_index()
                df.columns   = ['rango','categoria','conteo']
                df           = df[df['conteo']>0]
                df           = df.sort_values(by='categoria',ascending=True)
                df.index     = range(len(df))
                fig          = px.bar(df, x="rango", y="conteo", text="conteo", title="Áreas de los predios de transacciones")
                fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                
            with col2:
                df = dataprocesos_radio[dataprocesos_radio['preaconst'].notnull()]
                df = df[(df['cuantia']>0) & (df['preaconst']>0)]
                df['cuantia'] = df['cuantia']/df['preaconst']
                df            = getrango(df,'preaconst')
                df['conteo']  = 1
                df = df.groupby(['rango','categoria'])['cuantia'].median().reset_index()
                df.columns   = ['rango','categoria','cuantia']
                df           = df[df['cuantia']>0]
                df           = df.sort_values(by='categoria',ascending=True)
                df.index     = range(len(df))
                fig          = px.bar(df, x="rango", y="cuantia", text="cuantia", title="Cuantía por área de los predios")
                fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                
            with col1:
                df = dataprocesos_radio.groupby('year')['cuantia'].count().reset_index()
                df.columns = ['year','conteo']
                df['year']   = pd.to_numeric(df['year'],errors='coerce')
                df           = df[(df['conteo']>0) & (df['year']>0)]
                df           = df.sort_values(by='year',ascending=True)
                df.index     = range(len(df))
                df['year']   = df['year'].astype(int).astype(str)
                fig          = px.bar(df, x="year", y="conteo", text="conteo", title="Transacciones por año")
                fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                    
            with col2:
                df = dataprocesos_radio[dataprocesos_radio['cuantia'].notnull()]
                df = getrango(df,'cuantia')
                df['conteo'] = 1
                df = df.groupby(['rango','categoria'])['conteo'].count().reset_index()
                df.columns   = ['rango','categoria','conteo']
                df           = df[df['conteo']>0]
                df           = df.sort_values(by='categoria',ascending=True)
                df.index     = range(len(df))
                try: df['rango'] = df['rango'].apply(lambda x: f"${x:,.0f} MM")
                except: pass
                fig          = px.bar(df, x="rango", y="conteo", text="conteo", title="Transacciones por cuantía")
                fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
                fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
                 
    #-------------------------------------------------------------------------#
    # Informacion de mercado
    #-------------------------------------------------------------------------#
    tipoinmueble        = usosuelo2inmueble(usosuelo)
    datamarket_venta    = pd.DataFrame()
    datamarket_arriendo = pd.DataFrame()
    
    if tipoinmueble:
        inputvar = {'tipoinmueble':tipoinmueble,'polygon':str(polygonfilter)}
        datamarket_venta,datamarket_arriendo = getdatamarketcoddir(inputvar)

    # Venta
    display_datamarket(datamarket_venta,'venta',polygon=polygonfilter,latitud=latitud,longitud=longitud,downloadname="Descargar información")

    # Arriendo
    display_datamarket(datamarket_arriendo,'arriendo',polygon=polygonfilter,latitud=latitud,longitud=longitud,downloadname="Descargar información ")

    #-------------------------------------------------------------------------#
    # Analisis demografico
    display_dane(polygonfilter)
    