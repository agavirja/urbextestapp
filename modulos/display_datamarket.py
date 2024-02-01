import streamlit as st
import shapely.wkt as wkt
import plotly.express as px
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from bs4 import BeautifulSoup

from modulos.stylefunctions import style_function
from scripts.format_trimestre import format_trimestre

def display_datamarket(datamarket,tiponegocio,polygon=None,latitud=None,longitud=None,downloadname = "Descargar información"):

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
        
    if 'venta' in tiponegocio.lower():
        vardep = 'valorventa'
    elif 'arriendo' in tiponegocio.lower():
        vardep = 'valorarriendo'
    if not datamarket.empty:
        dataexport = datamarket.copy()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
          <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
          <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
        </head>
        <body>
        <div class="container-fluid py-1" style="margin-top: 0px;margin-bottom: 20px;">
          <div class="row">
            <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
              <div class="card">
                <div class="card-body p-3">
                  <div class="row">
                    <div class="numbers">
                      <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">Oferta en {tiponegocio.lower()}</h3>
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
        
        col1,col2,col3 = st.columns([2,1,1])
        
        with col1:
            dfmap   = datamarket.iloc[0:10,:].copy()
            m_market = folium.Map(location=[latitud, longitud], zoom_start=15,tiles="cartodbpositron")
         
            if polygon is not None:
                folium.GeoJson(polygon, style_function=style_function).add_to(m_market)
            
            img_style = '''
                    <style>               
                        .property-image{
                          flex: 1;
                        }
                        img{
                            width:200px;
                            height:120px;
                            object-fit: cover;
                            margin-bottom: 2px; 
                        }
                    </style>
                    '''
            for i, inmueble in dfmap.iterrows():
                if isinstance(inmueble['imagen_principal'], str) and len(inmueble['imagen_principal'])>20: imagen_principal =  inmueble['imagen_principal']
                else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
                url_export   = f"http://localhost:8501/Formato?code={inmueble['id']}&type=fichainmobiliaria" 
                if isinstance(inmueble['direccion'], str): direccion = inmueble['direccion'][0:35]
                else: direccion = '&nbsp'
                string_popup = f'''
                <!DOCTYPE html>
                <html>
                  <head>
                    {img_style}
                  </head>
                  <body>
                      <div>
                      <a href="{url_export}" target="_blank">
                      <div class="property-image">
                          <img src="{imagen_principal}"  alt="property image" onerror="this.src='https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png';">
                      </div>
                      </a>
                      {direccion}
                      <b> Precio: ${inmueble[vardep]:,.0f}</b><br>
                      <b> Área: {inmueble['areaconstruida']}</b><br>
                      </div>
                  </body>
                </html>
                '''
                folium.Marker(location=[inmueble["latitud"], inmueble["longitud"]], popup=string_popup).add_to(m_market)

            st_map = st_folium(m_market,width=800,height=500)

        with col2:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
              <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
            </head>
            <body>
            <div class="container-fluid py-1" style="margin-top: 0px;margin-bottom: -80px;">
              <div class="row">
                <div class="col-xl-12 col-sm-12 mb-xl-6 mb-6">
                  <div class="card">
                    <div class="card-body p-3">
                      <div class="row">
                        <div class="numbers">
                          <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">{len(datamarket)}</h3>
                          <p class="mb-0 text-capitalize" style="font-weight: 300;font-size: 1rem;text-align: center;">Ofertas en {tiponegocio} en el último año</p>
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
            
        with col3:
            try:    valor = f"${datamarket['valormt2'].median():,.0f}"
            except: valor = "Sin información"
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet" />
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet" />
              <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet" />
            </head>
            <body>
            <div class="container-fluid py-1" style="margin-top: 0px;margin-bottom: -80px;">
              <div class="row">
                <div class="col-xl-12 col-sm-12 mb-xl-6 mb-6">
                  <div class="card">
                    <div class="card-body p-3">
                      <div class="row">
                        <div class="numbers">
                          <h3 class="font-weight-bolder mb-0" style="text-align: center;font-size: 1.5rem;">{valor}</h3>
                          <p class="mb-0 text-capitalize" style="font-weight: 300;font-size: 1rem;text-align: center;">Valor promedio {tiponegocio} por mt2</p>
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
        
        with col2: 
            df = datamarket.copy()
            #df = df.set_index(['fecha_inicial'])
            #df  = df.groupby(pd.Grouper(freq='M'))['valormt2'].count().reset_index()
            #df.columns = ['fecha','count']
            
            df['trimestre'] = df['fecha_inicial'].dt.to_period("Q")
            df              = df.groupby('trimestre')['valormt2'].count().reset_index()
            df.columns      = ['fecha','count']
            df['fecha']     = df['fecha'].astype(str).apply(format_trimestre)
            df.index = range(len(df))
            fig      = px.bar(df, x="fecha", y="count", text="count", title=f"Histórico de ofertas en {tiponegocio}")
            fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', marker_color='#0095ff')
            fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")

        with col3:
            df = datamarket.copy()
            #df = df.set_index(['fecha_inicial'])
            #df  = df.groupby(pd.Grouper(freq='M'))['valormt2'].median().reset_index()
            #df.columns = ['fecha','valor']
            df['trimestre'] = df['fecha_inicial'].dt.to_period("Q")
            df              = df.groupby('trimestre')['valormt2'].median().reset_index()
            df.columns      = ['fecha','valor']
            df['fecha']     = df['fecha'].astype(str).apply(format_trimestre)
            df.index = range(len(df))
            fig      = px.bar(df, x="fecha", y="valor", text="valor", title=f"Histórico del valor por mt2 en {tiponegocio}")
            fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside', marker_color='#0095ff')
            fig.update_layout(title_x=0.2,height=400, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True,sharing="streamlit", theme="streamlit")
        
        market_imagenes = ''
        for i, inmueble in dfmap.iterrows():
            if isinstance(inmueble['imagen_principal'], str) and len(inmueble['imagen_principal'])>20: imagen_principal =  inmueble['imagen_principal']
            else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
            url_export   = f"http://localhost:8501/Formato?code={inmueble['id']}&type=fichainmobiliaria" 
            if isinstance(inmueble['direccion'], str): direccion = inmueble['direccion'][0:35]
            else: direccion = '&nbsp'
                
            market_imagenes += f'''    
              <div class="propiedad">
                <a href="{url_export}" target="_blank">
                <div class="imagen">
                  <img src="{imagen_principal}">
                </div>
                </a>
                <div class="caracteristicas">
                  <h3>${inmueble[vardep]:,.0f} | <strong>{inmueble["areaconstruida"]}</strong> mt<sup>2</sup></h3>
                  <p>Dirección: {direccion}</p>
                </div>
              </div>
              ''' 
        if market_imagenes!="":  
            style = """
                <style>
                  .contenedor-propiedades {
                    overflow-x: scroll;
                    white-space: nowrap;
                    margin-bottom: 40px;
                    margin-top: 30px;
                  }
                  .propiedad {
                    display: inline-block;
                    vertical-align: top;
                    margin-right: 20px;
                    text-align: center;
                    width: 300px;
                  }
                  .imagen {
                    height: 200px;
                    margin-bottom: 10px;
                    overflow: hidden;
                  }
                  .imagen img {
                    display: block;
                    height: 100%;
                    width: 100%;
                    object-fit: cover;
                  }
                  .caracteristicas {
                    background-color: #f2f2f2;
                    padding: 4px;
                    text-align: left;
                  }
                  .caracteristicas h3 {
                    font-size: 18px;
                    margin-top: 0;
                  }
    
                </style>
            """
        
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-icons.css" rel="stylesheet">
              <link href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/nucleo-svg.css" rel="stylesheet">
              <link id="pagestyle" href="https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/css/soft-ui-dashboard.css?v=1.0.7" rel="stylesheet">
              {style}
            </head>
            <body>
              <div class="container-fluid py-4" style="margin-top: -50px;margin-bottom: 20px;">
                <div class="row">
                  <div class="col-xl-12 col-sm-6 mb-xl-0 mb-2">
                    <div class="card">
                      <div class="card-body p-3">            
                        <div class="container-fluid py-2">
                          <div class="row">
                            <div class="contenedor-propiedades">
                                {market_imagenes}
                            </div>                      
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

        variables = ['direccion', 'imagen_principal', 'fecha_inicial', 'areaconstruida', 'valorventa', 'valorarriendo', 'habitaciones', 'banos', 'garajes', 'estrato', 'antiguedad', 'valormt2']
        variables = [x for x in variables if x in dataexport]
        if variables:
            dataexport = dataexport[variables]
            dataexport.rename(columns={'direccion': 'Direccion', 'imagen_principal': 'imagen', 'fecha_inicial': 'Fecha inicial', 'areaconstruida': 'Area construida', 'valorventa': 'Valor de venta', 'valorarriendo': 'Valor de arriendo', 'habitaciones': 'Habitaciones', 'banos': 'Banos', 'garajes': 'Garajes', 'estrato': 'Estrato', 'antiguedad': 'Antiguedad', 'valormt2': 'valor por mt2'},inplace=True)
            col1, col2 = st.columns([3,1])
            with col2:
                csv = convert_df(dataexport)     
                st.download_button(
                   downloadname,
                   csv,
                   f"data_info_market_{tiponegocio.lower()}.csv",
                   "text/csv"
                )

def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')
