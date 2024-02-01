import streamlit as st
import pandas as pd
import numpy as np
import re
import json
import requests
import shapely.wkt as wkt
import copy
from sqlalchemy import create_engine 
from shapely.geometry import Polygon,Point,mapping,shape,box
from unidecode import unidecode
from io import BytesIO
from PIL import Image
from multiprocessing.dummy import Pool
from datetime import datetime

from scripts.formato_direccion import formato_direccion


#-----------------------------------------------------------------------------#
@st.cache_data
def getdatasnr(chip):
    
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    query    = None
    
    datamatricula = pd.DataFrame()
    datasnr       = pd.DataFrame()
    datatable     = pd.DataFrame()
    dataprocesos  = pd.DataFrame()
    
    if isinstance(chip, list):
        query = "','".join(chip)
        query = f" numeroChip IN ('{query}')"
    elif isinstance(chip, str):
        query =  f" numeroChip='{chip}'"
    
    if query:
        datamatricula = pd.read_sql_query(f"SELECT numeroChip as prechip,numeroMatriculaInmobiliaria as matricula FROM  bigdata.data_bogota_catastro_predio WHERE {query}" , engine)
        datamatricula = datamatricula.drop_duplicates()
    
    if not datamatricula.empty:
        query     = "','".join(datamatricula['matricula'].astype(str).unique())
        query     = f" value IN ('{query}')"
        datasnr   = pd.read_sql_query(f"SELECT docid,value as matricula FROM  bigdata.snr_data_matricula WHERE {query}" , engine)
        
    if not datasnr.empty:
        query     = "','".join(datasnr['docid'].astype(str).unique())
        query     = f" docid IN ('{query}') AND oficina LIKE '%bogota%' AND entidad LIKE '%bogota%'"
        datatable = pd.read_sql_query(f"SELECT docid, fecha_documento_publico,tipo_documento_publico, numero_documento_publico,datos_solicitante,documento_json,entidad FROM  bigdata.snr_data_completa WHERE {query}" , engine)
        datatable = add2tablaSNR(datatable)
        variables = [x for x in ['docid', 'fecha_documento_publico', 'tipo_documento_publico', 'numero_documento_publico','entidad'] if x in datatable]
        datatable = datatable[variables]
        datamerge = datasnr[datasnr['docid'].isin(datatable['docid'])]
        datatable = datamerge.merge(datatable,on='docid',how='left',validate='m:1')
    
    if not datatable.empty:
        query        = "','".join(datatable['docid'].astype(str).unique())
        query        = f" docid IN ('{query}')"
        dataprocesos = pd.read_sql_query(f"SELECT docid,codigo,nombre,tarifa,cuantia FROM  bigdata.snr_tabla_procesos WHERE {query}" , engine)
        dataprocesos = dataprocesos.drop_duplicates()
        datamerge    = datamatricula.drop_duplicates(subset='matricula',keep='first')
        datatable    = datatable.merge(datamerge,on='matricula',how='left',validate='m:1')
        
    if not dataprocesos.empty:
        datamerge    = datatable.sort_values(by=['docid','fecha_documento_publico'],ascending=False).drop_duplicates(subset=['docid'],keep='first')
        dataprocesos = dataprocesos.merge(datamerge[['docid','fecha_documento_publico','tipo_documento_publico','numero_documento_publico','entidad']],on='docid',how='left',validate='m:1')
        dataprocesos['link'] = dataprocesos['docid'].apply(lambda x: f'https://radicacion.supernotariado.gov.co/app/static/ServletFilesViewer?docId={x}')
        dataprocesos['fecha_documento_publico'] = dataprocesos['fecha_documento_publico'].dt.strftime('%Y-%m-%d')
        dataprocesos = dataprocesos.sort_values(by='fecha_documento_publico',ascending=False)
    engine.dispose()
    # datatable:    Todas las matriculas asociadas a un mismo docid
    # dataprocesos: Todas los procesos asociados a un docid
    return dataprocesos,datatable


#-----------------------------------------------------------------------------#
@st.cache_data
def getinfopolygon(polygon,precuso):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    schema   = st.secrets["schema_bigdata"]
    
    dataimport             = pd.DataFrame()
    datacatastro           = pd.DataFrame()
    datashd                = pd.DataFrame()
    dataSNR                = pd.DataFrame()
    datamatriculaSNR       = pd.DataFrame()
    datatable              = pd.DataFrame()
    dataestadisticas       = pd.DataFrame()
    
    engine     = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    datapoints = pd.read_sql_query(f"SELECT lotcodigo FROM  bigdata.data_bogota_lotes_point WHERE ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'), POINT(longitud, latitud))" , engine)
    if not datapoints.empty:
        query      = "','".join(datapoints['lotcodigo'].unique())
        query      = f" lotcodigo IN ('{query}')"        
        dataimport = pd.read_sql_query(f"SELECT lotcodigo as barmanpre, ST_AsText(geometry) as wkt FROM  bigdata.data_bogota_lotes WHERE {query}" , engine)
    
        # Remover vias
        query               = "','".join(datapoints['lotcodigo'].unique())
        query               = f" barmanpre IN ('{query}')"          
        datacatastro_novias = pd.read_sql_query(f"SELECT  barmanpre  FROM  bigdata.data_bogota_catastro WHERE precdestin IN ('65','66') AND {query}" , engine)
        idd          = dataimport['barmanpre'].isin(datacatastro_novias['barmanpre'])
        if sum(idd)>0:
            dataimport = dataimport[~idd]
            
    #-------------------------------------------------------------------------#
    # Data catastro
    if not dataimport.empty:
        query        = "','".join(dataimport['barmanpre'].unique())
        query        = f" barmanpre IN ('{query}')" 
        if precuso!=[]:
            precusolist  = "','".join(precuso)
            query       += f" AND precuso IN ('{precusolist}')"

        datacatastro = pd.read_sql_query(f"SELECT id,precbarrio,prenbarrio,prechip,predirecc,preaterre,preaconst,precdestin,precuso,preuvivien,preusoph,prevetustz,barmanpre,latitud,longitud,coddir,piso,estrato  FROM  bigdata.data_bogota_catastro WHERE {query} AND (precdestin<>'65')" , engine)
        dataprecuso,dataprecdestin = getuso_destino()
        dataprecuso.rename(columns={'codigo':'precuso','tipo':'usosuelo','descripcion':'desc_usosuelo'},inplace=True)
        dataprecdestin.rename(columns={'codigo':'precdestin','tipo':'actividad','descripcion':'desc_actividad'},inplace=True)
        datacatastro = datacatastro.merge(dataprecuso,on='precuso',how='left',validate='m:1')
        datacatastro = datacatastro.merge(dataprecdestin,on='precdestin',how='left',validate='m:1')
        datacatastro['formato_direccion'] = datacatastro['predirecc'].apply(lambda x: formato_direccion(x))
        for i in ['preaconst','preaterre']:
            idd = datacatastro[i].isnull()
            if sum(idd)>0:
                datacatastro.loc[idd,i] = 0
    engine.dispose()
        
    #-------------------------------------------------------------------------#
    # Data shd
    if not datacatastro.empty:
        datashd      = getdatacapital_sdh(list(datacatastro['prechip'].unique()))
        datashdmerge = datashd.copy()
        datashdmerge = datashdmerge[datashdmerge['valorAutoavaluo']>0]
        datashdmerge = datashdmerge.sort_values(by=['chip','vigencia','valorAutoavaluo'],ascending=False)
        datashdmerge = datashdmerge.groupby('chip').agg({'valorAutoavaluo':'first','valorImpuesto':'first'}).reset_index()
        datashdmerge.columns = ['prechip','avaluocatastral','predial']
        datacatastro = datacatastro.merge(datashdmerge,on='prechip',how='left',validate='m:1')
        datacatastro['avaluoxmt2']  = datacatastro['avaluocatastral']/datacatastro['preaconst']
        datacatastro['predialxmt2'] = datacatastro['predial']/datacatastro['preaconst']  

    if not dataimport.empty  and not datacatastro.empty:
        datagrupada = groupcatastro(datacatastro)
        datagrupada['merge'] = 1
        dataimport  = dataimport.merge(datagrupada,on='barmanpre',how='left',validate='m:1')
        dataimport  = dataimport[dataimport['merge']==1]
        dataimport.drop(columns=['merge'],inplace=True)
            
    #-------------------------------------------------------------------------#
    # Data SNR     
    if datacatastro.empty is False:
        query   = "','".join(datacatastro['prechip'].astype(str).unique())
        query   = f" numeroChip IN ('{query}')"
        dataSNR = pd.read_sql_query(f"SELECT numeroChip as prechip,numeroMatriculaInmobiliaria as matricula FROM  bigdata.data_bogota_catastro_predio WHERE {query}" , engine)
        dataSNR = dataSNR.drop_duplicates()
        
    if dataSNR.empty is False:
        query            = "','".join(dataSNR['matricula'].astype(str).unique())
        query            = f" value IN ('{query}')"
        datamatriculaSNR = pd.read_sql_query(f"SELECT docid,value as matricula FROM  bigdata.snr_data_matricula WHERE {query}" , engine)
        
    if datamatriculaSNR.empty is False:
        datamatriculaSNR = datamatriculaSNR.drop_duplicates()
        dataSNR      = datamatriculaSNR.merge(dataSNR,on='matricula',how='left',validate='m:1')
        query        = "','".join(dataSNR['docid'].astype(str).unique())
        query        = f" docid IN ('{query}') AND codigo IN ('125','126','168','169','0125','0126','0168','0169')"
        dataprocesos = pd.read_sql_query(f"SELECT docid,codigo,nombre,tarifa,cuantia FROM  bigdata.snr_tabla_procesos WHERE {query}" , engine)
        dataprocesos = dataprocesos.sort_values(by=['docid','cuantia'],ascending=False).drop_duplicates(subset='docid',keep='first')
        dataprocesos = dataprocesos[dataprocesos['tarifa'].str.contains('100%')]
        dataprocesos = dataprocesos.drop_duplicates(subset=['docid','tarifa','cuantia'])
        dataSNR   = dataSNR.merge(dataprocesos,on='docid',how='left',validate='m:1')
        dataSNR   = dataSNR[dataSNR['codigo'].notnull()]
        dataSNR   = dataSNR.merge(datacatastro,on='prechip',how='left',validate='m:1')
        query     = "','".join(dataSNR['docid'].astype(str).unique())
        query     = f" docid IN ('{query}') AND oficina LIKE '%bogota%' AND entidad LIKE '%bogota%'"  
        datatable = pd.read_sql_query(f"SELECT docid, fecha_documento_publico,tipo_documento_publico, numero_documento_publico,datos_solicitante,documento_json,entidad FROM  bigdata.snr_data_completa WHERE {query}" , engine)
            
    if datatable.empty is False:
        datatable = add2tablaSNR(datatable)
        variables = [x for x in ['docid', 'fecha_documento_publico', 'tipo_documento_publico', 'numero_documento_publico','entidad'] if x in datatable]
        datatable = datatable[variables]
        dataSNR   = dataSNR.merge(datatable,on='docid',how='left',validate='m:1')

    if dataSNR.empty is False:
        variables = [x for x in ['docid', 'nombre', 'cuantia', 'prenbarrio', 'predirecc','preaterre', 'preaconst', 'preusoph', 'prevetustz', 'barmanpre', 'estrato', 'usosuelo', 'desc_usosuelo', 'actividad', 'desc_actividad', 'formato_direccion', 'avaluocatastral', 'predial', 'fecha_documento_publico', 'tipo_documento_publico', 'numero_documento_publico','entidad'] if x in dataSNR]
        dataSNR   = dataSNR[variables]
        dataSNR['link']          = dataSNR['docid'].apply(lambda x: f'https://radicacion.supernotariado.gov.co/app/static/ServletFilesViewer?docId={x}')
        dataSNR['valormt2venta'] = dataSNR['cuantia']/dataSNR['preaconst']
        dataSNR['fecha_documento_publico'] = dataSNR['fecha_documento_publico'].dt.strftime('%Y-%m-%d')
        if not dataimport.empty:
            try:
                df = dataSNR.groupby('barmanpre')['docid'].count().reset_index()
                df.columns = ['barmanpre','transacciones']
                dataimport = dataimport.merge(df,on='barmanpre',how='left',validate='m:1')
            except: 
                dataimport['transacciones'] = None
                
    #-------------------------------------------------------------------------#
    # Estadisticas
    if datacatastro.empty is False:
        formato = [{'variable':'preaconst','name':'areaconstruida'},
                   {'variable':'avaluocatastral','name':'avaluocatastral'},
                   {'variable':'avaluoxmt2','name':'avaluoxmt2'},
                   {'variable':'prevetustz','name':'antiguedad'},]
        
        for j in formato:
            df = getrango(datacatastro.copy(),j['variable'])
            if not df.empty:
                df['conteo'] = 1
                datapaso             = df.groupby(['rango','categoria'])['conteo'].count().reset_index()
                datapaso.columns     = ['index','categoria','value']
                datapaso['variable'] = j['name']
                datapaso             = datapaso[datapaso['value']>0]
                dataestadisticas     = pd.concat([dataestadisticas,datapaso])

    return datacatastro,dataimport,dataestadisticas,dataSNR

def addvalue(x,y):
    try:
        x = json.loads(x)
        x.append({'variable': 'merge', 'value': y})
    except: pass
    return x

def add2tablaSNR(datatable):
    datatable = datatable.drop_duplicates()
    datatable['fecha_documento_publico'] = pd.to_datetime(datatable['fecha_documento_publico'],errors='coerce')
    idd       = datatable['fecha_documento_publico'].isnull()
    
    # Los que tienen fecha nula
    if sum(idd)>0:
        datatable['merge']   = range(len(datatable))
        datapaso                 = datatable[idd]
        datapaso['fechanotnull'] = datapaso['documento_json'].apply(lambda x: getEXACTfecha(x))
        formato_fecha = '%d-%m-%Y'
        datapaso['fechanotnull'] = pd.to_datetime(datapaso['fechanotnull'],format=formato_fecha,errors='coerce')
        datatable  = datatable.merge(datapaso[['merge','fechanotnull']],how='left',validate='m:1')
        idd = (datatable['fecha_documento_publico'].isnull()) & (datatable['fechanotnull'].notnull())
        if sum(idd)>0:
            datatable.loc[idd,'fecha_documento_publico'] = datatable.loc[idd,'fechanotnull']
        datatable.drop(columns=['fechanotnull','merge'],inplace=True)
    return datatable

def getrango(df,variable):
    addlabel   = ''
    if  any([x for x in ['preaconst','preaterre','areaconstruida'] if x in variable]):
        addlabel = ' mt2'
    elif 'avaluocatastral' in variable:
        addlabel = 'millones'
        df[variable] = df[variable]/1000000
    elif 'avaluoxmt2' in variable:
        addlabel = 'millones'
        df[variable] = df[variable]/1000000
    elif 'cuantia' in variable:
        addlabel = 'millones'
        df[variable] = df[variable]/1000000
    if 'prevetustz' in variable:
        df['antiguedad'] = datetime.now().year-df['prevetustz']
        variable = 'antiguedad'
        
    idd = np.isinf(df[variable]) | np.isneginf(df[variable]) | (df[variable].isnull())
    df  = df[~idd]

    if not df.empty:
        df = df.sort_values(by=variable,ascending=True)
        try:
            df          = df.sort_values(by=variable,ascending=True)
            total_rows  = len(df)
            df.index    = range(len(df))
            percentages = [0.25, 0.35, 0.20, 0.12, 0.08]
            limits = [0] + [int(p * total_rows) for p in percentages[:-1]]
            limits = list(np.cumsum(limits))+[total_rows]
            labels = []
            for i in range(len(limits) - 1):
                start_val = int(df.loc[limits[i], variable])
                end_val = int(df.loc[limits[i + 1] - 1, variable])
                if any([x for x in ['avaluocatastral','avaluoxmt2','cuantia'] if x in variable]):
                    start_val = f'${start_val:,.0f}'
                    end_val   = f'${end_val:,.0f}'
                labels.append(f"{start_val}-{end_val} {addlabel}")
            df['rango']     = pd.cut(df.index,bins=limits,labels=labels,include_lowest=True)
            df['categoria'] = pd.cut(df.index,bins=limits,labels=[1,2,3,4,5],include_lowest=True)
        except:
            try:
                Q1              = df[variable].quantile(0.025)
                Q3              = df[variable].quantile(0.975)
                IQR             = Q3 - Q1
                limite_inferior = Q1 - 1.5 * IQR
                limite_superior = Q3 + 1.5 * IQR
                
                num_values  = 5
                idd         = (df[variable] >= limite_inferior) & (df[variable] <= limite_superior)
                dfnew       = df[idd]
                hist, bins  = np.histogram(dfnew[variable], bins=num_values)
                bins[0]     = 0
                bins[-1]    = np.inf
                cuantiles, bins = pd.cut(df[variable],bins, labels=False, retbins=True)
                
                if 'avaluocatastral' in variable:
                    addlabel = 'mm'
                    labels = [f'Menor a ${int(round(bins[1], 0)/1000000)} {addlabel}' if i == 0 else f'${int(round(bins[i], 0)/1000000)} a ${int(round(bins[i+1], 0)/1000000)} {addlabel}' for i in range(num_values - 1)]
                    labels.append(f'Mayor a ${int(round(bins[-2], 0)/1000000)} {addlabel}')
                elif 'avaluoxmt2' in variable:
                    addlabel = 'mm'
                    labels = [f'Menor a ${round(bins[1]/1000000, 1)} {addlabel}' if i == 0 else f'${round(bins[i]/1000000, 1)} a ${round(bins[i+1]/1000000, 1)} {addlabel}' for i in range(num_values - 1)]
                    labels.append(f'Mayor a ${round(bins[-2]/1000000, 1)} {addlabel}')
                elif 'cuantia' in variable:
                    addlabel = 'mm'
                    labels = [f'Menor a ${int(round(bins[1], 0)/1000000)} {addlabel}' if i == 0 else f'${int(round(bins[i], 0)/1000000)} a ${int(round(bins[i+1], 0)/1000000)} {addlabel}' for i in range(num_values - 1)]
                    labels.append(f'Mayor a ${int(round(bins[-2], 0)/1000000)} {addlabel}')
                else:
                    labels = [f'Menor a {int(round(bins[1], 0))} {addlabel}' if i == 0 else f'{int(round(bins[i], 0))} a {int(round(bins[i+1], 0))} {addlabel}' for i in range(num_values - 1)]
                    labels.append(f'Mayor a {int(round(bins[-2], 0))} {addlabel}')
                df['rango'] = pd.cut(df[variable],bins, labels=labels)
                df['categoria'] = pd.cut(df[variable],bins, labels=[1,2,3,4,5])
            except: 
                df['rango'] = df[variable].copy()
                df['categoria'] = 1
    else:
        df = pd.DataFrame()
    return df

def getEXACTfecha(x):
    result = None
    try:
        x = json.loads(x)
        continuar = 0
        for i in ['fecha','fecha:','fecha expedicion','fecha expedicion:','fecha recaudo','fecha recaudo:']:
            for j in x:
                if i==re.sub('\s+',' ',unidecode(j['value'].lower())):
                    posicion = x.index(j)
                    result   = x[posicion+1]['value']
                    continuar = 1
                    break
            if continuar==1:
                break
    except: result = None
    if result is None:
        result = getINfecha(x)
    return result
    
def getINfecha(x):
    result = None
    try:
        x = json.loads(x)
        continuar = 0
        for i in ['fecha','fecha:','fecha expedicion','fecha expedicion:','fecha recaudo','fecha recaudo:']:
            for j in x:
                if i in re.sub('\s+',' ',unidecode(j['value'].lower())):
                    posicion = x.index(j)
                    result   = x[posicion+1]['value']
                    continuar = 1
                    break
            if continuar==1:
                break
    except: result = None
    return result
    
    
#-----------------------------------------------------------------------------#
@st.cache_data
def getinfoBarmanpre(barmanpre):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    schema   = st.secrets["schema_bigdata"]
    
    engine       = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    datacatastro = pd.read_sql_query(f"SELECT predirecc,precuso,precdestin,preaconst,preaterre,prevetustz,preusoph  FROM  bigdata.data_bogota_catastro WHERE barmanpre='{barmanpre}' AND (precdestin<>'65')" , engine)
    dataprecuso,dataprecdestin = getuso_destino()
    dataprecuso.rename(columns={'codigo':'precuso','tipo':'usosuelo','descripcion':'desc_usosuelo'},inplace=True)
    dataprecdestin.rename(columns={'codigo':'precdestin','tipo':'actividad','descripcion':'desc_actividad'},inplace=True)
    datacatastro = datacatastro.merge(dataprecuso,on='precuso',how='left',validate='m:1')
    datacatastro = datacatastro.merge(dataprecdestin,on='precdestin',how='left',validate='m:1')
    datacatastro['formato_direccion'] = datacatastro['predirecc'].apply(lambda x: formato_direccion(x))
    for i in ['preaconst','preaterre']:
        idd = datacatastro[i].isnull()
        if sum(idd)>0:
            datacatastro.loc[idd,i] = 0
    engine.dispose()

    return datacatastro
#-----------------------------------------------------------------------------#
@st.cache_data
def getdatacapital_sdh(chip):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    schema   = st.secrets["schema_bigdata"]
    engine   = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    datashd  = pd.DataFrame()
    
    if isinstance(chip, list):
        df       = pd.DataFrame({'chip':chip})
        df.index = range(len(df))
        futures  = [] 
        pool     = Pool(10)
        batches  = np.array_split(df, len(df) // 1000 + 1)      
        for batch in batches:
            futures.append(pool.apply_async(readdata_sdh,args = (engine,batch, )))
        for future in futures:
            #datashd = datashd.append(future.get())
            datashd = pd.concat([datashd,future.get()])
            
    elif isinstance(chip, str):
        query   =  'chip="{chip}"'
        datashd = pd.read_sql_query(f"SELECT chip,vigencia,valorAutoavaluo,valorImpuesto,direccionPredio,nroIdentificacion,indPago,idSoporteTributario FROM bigdata.data_bogota_catastro_vigencia WHERE {query}" , engine)
    
    engine.dispose()   
    return datashd

def readdata_sdh(engine,batch):
    query = "','".join(batch['chip'])
    query = f" chip IN ('{query}')"
    data  = pd.read_sql_query(f"SELECT chip,vigencia,valorAutoavaluo,valorImpuesto,direccionPredio,nroIdentificacion,indPago,idSoporteTributario FROM bigdata.data_bogota_catastro_vigencia WHERE {query}" , engine)
    return data
#-----------------------------------------------------------------------------#
@st.cache_data
def groupcatastro(df):
    w     = {'formato_direccion':'first','barmanpre':'count','prenbarrio':'first','prevetustz':['min','max'],'estrato':'median','preaconst':'sum','preaterre':'sum','usosuelo': lambda x: list(x.unique()),'actividad':lambda x: list(x.unique())}
    lista = ['barmanpre','direccion','predios','barrio','antiguedad_min','antiguedad_max','estrato','areaconstruida','areaterreno','usosuelo','actividad']
    for i in ['avaluocatastral','avaluoxmt2','predialxmt2']:
        if i in df:
            w.update({i:'median'})
            lista.append(i)
            
    df = df.groupby(['barmanpre']).agg(w).reset_index()
    df.columns = lista
    return df
#-----------------------------------------------------------------------------#
@st.cache_data
def getuso_destino():
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    schema   = st.secrets["schema_bigdata"]
    
    engine         = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    dataprecuso    = pd.read_sql_query("SELECT * FROM  bigdata.bogota_catastro_precuso" , engine)
    dataprecdestin = pd.read_sql_query("SELECT * FROM  bigdata.bogota_catastro_precdestin" , engine)
    engine.dispose()
    return dataprecuso,dataprecdestin
#-----------------------------------------------------------------------------#
@st.cache_data
def tipoinmueble2PrecUso():
    formato = {
        'Apartamento':['001','002','037','038'],
        'Bodega':['001','008','009','010','012','014','019','025','028','032','033','037','044','053','066','080','081','091','093','097',],
        'Casa':['001','037'],
        'Local':['003','004','006','007','008','009','010','012','019','025','028','039','040','041','042','044','056','057','060','080','081','091','093','094','095'],
        'Oficina':['005','006','015','018','020','041','045','080','081','082','092','094','095','096'],
        'Parqueadero':['005','024','048','049','050','096'],
        'Consultorio':['015','017','020','043','045','092'],
        'Edificio':['024','050'],
        'Hotel':['021','026','027','046'],
        'Lote':['090','000'],
        }
    return formato

#-----------------------------------------------------------------------------#
@st.cache_data
def getusedmarket(polygon,tipoinmueble):
    
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    datamarket_venta    = pd.DataFrame()
    datamarket_arriendo = pd.DataFrame()
    try:
        schema = "market"
        engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
        if any([x for x in ['apartamento','casa','consultorio','bodega','edificio','local','lote','hotel','oficina'] if x in tipoinmueble.lower()]):
            datamarket_venta    = pd.read_sql_query(f"SELECT fecha_inicial,areaconstruida,	valorventa,	valorarriendo, valormt2,inmobiliaria,latitud,longitud,id as code,direccion,imagen_principal FROM  {schema}.data_ofertas_venta_{tipoinmueble.lower()}_bogota WHERE ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'), geometry)" , engine)
            datamarket_arriendo = pd.read_sql_query(f"SELECT fecha_inicial,areaconstruida,	valorventa,	valorarriendo, valormt2,inmobiliaria,latitud,longitud,id as code,direccion,imagen_principal FROM  {schema}.data_ofertas_arriendo_{tipoinmueble.lower()}_bogota WHERE ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'), geometry)" , engine)
            datamarket_venta['tipoinmueble']    = tipoinmueble
            datamarket_arriendo['tipoinmueble'] = tipoinmueble

        elif 'todos' in tipoinmueble.lower():
            datamarket_venta    = pd.DataFrame()
            datamarket_arriendo = pd.DataFrame()
            for tipoinmueble in ['apartamento','casa','consultorio','bodega','edificio','local','lote','hotel','oficina']:
                try:
                    datapasoventa    = pd.read_sql_query(f"SELECT fecha_inicial,areaconstruida,	valorventa,	valorarriendo, valormt2,inmobiliaria,latitud,longitud,id as code,direccion,imagen_principal FROM  {schema}.data_ofertas_venta_{tipoinmueble.lower()}_bogota WHERE ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'), geometry)" , engine)
                    datapasoarriendo = pd.read_sql_query(f"SELECT fecha_inicial,areaconstruida,	valorventa,	valorarriendo, valormt2,inmobiliaria,latitud,longitud,id as code,direccion,imagen_principal FROM  {schema}.data_ofertas_arriendo_{tipoinmueble.lower()}_bogota WHERE ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'), geometry)" , engine)
                    if not datapasoventa.empty: 
                        datapasoventa['tipoinmueble'] = tipoinmueble
                        datamarket_venta = pd.concat([datamarket_venta,datapasoventa])
                        datamarket_venta['tipoinmueble'] = tipoinmueble
                    if not datapasoarriendo.empty: 
                        datapasoarriendo['tipoinmueble'] = tipoinmueble
                        datamarket_arriendo = pd.concat([datamarket_arriendo,datapasoarriendo])
                        datamarket_arriendo['tipoinmueble'] = tipoinmueble
                except: pass
        engine.dispose()
        if not datamarket_venta.empty: 
            datamarket_venta                  = datamarket_venta[datamarket_venta['valormt2']>0]
            datamarket_venta['tiponegocio']   = 'Venta'
            datamarket_venta['fecha_inicial'] = pd.to_datetime(datamarket_venta['fecha_inicial'],errors='coerce')
            #datamarket_venta = datamarket_venta.sort_values(by='fecha_inicial',ascending=True).drop_duplicates(subset=['areaconstruida','valormt2','inmobiliaria'])
            datamarket_venta = datamarket_venta.sort_values(by='fecha_inicial',ascending=True).drop_duplicates(subset=['areaconstruida','valorventa','tipoinmueble'])

        if not datamarket_arriendo.empty: 
            datamarket_arriendo                = datamarket_arriendo[datamarket_arriendo['valormt2']>0]
            datamarket_arriendo['tiponegocio'] = 'Arriendo'
            datamarket_arriendo['fecha_inicial'] = pd.to_datetime(datamarket_arriendo['fecha_inicial'],errors='coerce')
            #datamarket_arriendo = datamarket_arriendo.sort_values(by='fecha_inicial',ascending=True).drop_duplicates(subset=['areaconstruida','valormt2','inmobiliaria'])
            datamarket_arriendo = datamarket_arriendo.sort_values(by='fecha_inicial',ascending=True).drop_duplicates(subset=['areaconstruida','valorarriendo','tipoinmueble'])
    except: pass
    return datamarket_venta,datamarket_arriendo
    
#-----------------------------------------------------------------------------#
# Galeria Inmobiliaria Nuevos

@st.cache_data
def get_proyectos_datapoints(polygon):
    user     = st.secrets["user_bigdata"]
    password = st.secrets["password_bigdata"]
    host     = st.secrets["host_bigdata_lectura"]
    schema   = st.secrets["schema_bigdata"]
    
    # polygon       = """POLYGON((-74.055778 4.693639, -74.057779 4.680018, -74.041968 4.688398, -74.050962 4.692795, -74.055778 4.693639))"""
    engine        = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{schema}')
    datapoints    = pd.read_sql_query(f"""SELECT codproyecto,latitud,longitud FROM bigdata.data_bogota_gi_nueva_latlng WHERE ST_CONTAINS(ST_GEOMFROMTEXT('{polygon}'),POINT(longitud,latitud))""", engine)
    dataproyecto  = pd.DataFrame()
    datainmuebles = pd.DataFrame()
    datahistorico = pd.DataFrame()
    dataestadisticas =  pd.DataFrame()
    
    if not dataproyecto.empty:
        dataproyecto['estado'] = dataproyecto['estado'].replace(['Term./'],['Terminado'])
        
    if not datapoints.empty:
        query         = "','".join(datapoints['codproyecto'].astype(str).unique())
        query         = f" codproyecto IN ('{query}')"        
        dataproyecto  = pd.read_sql_query(f"""SELECT * FROM bigdata.data_bogota_gi_nueva_proyectos WHERE {query}""", engine)
        datainmuebles = pd.read_sql_query(f"""SELECT * FROM bigdata.data_bogota_gi_nueva_formulada WHERE {query}""", engine)

        if datainmuebles.empty is False: 
            query         = "','".join(datainmuebles['codinmueble'].astype(str).unique())
            query         = f" codinmueble IN ('{query}')"        
            datahistorico = pd.read_sql_query(f"""SELECT * FROM bigdata.data_bogota_gi_nueva_long WHERE {query}""" , engine)
    engine.dispose()
    
    datapoints['geometry'] = None
    if not datapoints.empty and not dataproyecto.empty:
        df         = dataproyecto[['codproyecto','proyecto','vende','construye','direccion','fecha_inicio','estado','financiera','unidades_proyecto']]
        datapoints = datapoints.merge(df,on='codproyecto',how='left',validate='m:1')
        
    if not datapoints.empty:
        datapoints['geometry'] = datapoints.apply(lambda row: square_polygon(5,row['latitud'], row['longitud']), axis=1)
        
    if not datahistorico.empty:        
        idx              = datahistorico.groupby('codinmueble').head(1).index
        dataestadisticas = datahistorico.loc[idx]
        try: 
            dataestadisticas  = dataestadisticas.merge(datainmuebles[['codinmueble','areaconstruida']],on='codinmueble',how='left',validate='1:1')
            dataestadisticas['valormt2'] = dataestadisticas['valor_P']/dataestadisticas['areaconstruida']
        except: pass
        try: 
            dataestadisticas  = dataestadisticas.merge(dataproyecto[['codproyecto','activo','estado']],on='codproyecto',how='left',validate='m:1')
        except: pass        
            

    return datapoints,dataproyecto,datainmuebles,datahistorico,dataestadisticas

def square_polygon(metros, lat, lng):

    half_side_deg  = (metros / 1000.0) / 111.32  
    top_left       = [lng - half_side_deg, lat + half_side_deg]
    top_right      = [lng + half_side_deg, lat + half_side_deg]
    bottom_right   = [lng + half_side_deg, lat - half_side_deg]
    bottom_left    = [lng - half_side_deg, lat - half_side_deg]
    square_polygon = Polygon([top_left, top_right, bottom_right, bottom_left, top_left])
    return square_polygon

#-----------------------------------------------------------------------------#
# Censo demografico DANE
@st.cache_data
def censodane(polygon):
    try:
        # https://geoportal.dane.gov.co/geovisores/territorio/analisis-cnpv-2018/
        coordenadas = re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", polygon)
        coordenadas = coordenadas[:-1]
        coordenadas = ",".join([f"{lon},{lat}" for lon, lat in coordenadas])
        url = f"https://geoportal.dane.gov.co/laboratorio/serviciosjson/poblacion/20221215-indicadordatospoligonos.php?coordendas={coordenadas}"
        r   = requests.get(url,verify=False, timeout=20).json()
        df  = pd.DataFrame(r)
        df.rename(columns={'V1': 'Total viviendas', 'V2': 'Uso mixto', 'V3': 'Unidad no residencial', 'V4': 'Lugar especial de alojamiento - LEA', 'V5': 'Industria (uso mixto)', 'V6': 'Comercio (uso mixto)', 'V7': 'Servicios (uso mixto)', 'V8': 'Agropecuario, agroindustrial, foresta (uso mixto)', 'V9': 'Sin información (uso mixto)', 'V10': 'Industria (uso no residencial)', 'V11': 'Comercio (uso no residencial)', 'V12': 'Servicios (uso no residencial)', 'V13': 'Agropecuario, Agroindustrial, Foresta (uso no residencial)', 'V14': 'Institucional (uso no residencial)', 'V15': 'Lote (Unidad sin construcción)', 'V16': 'Parque/ Zona Verde (uso no residencial)', 'V17': 'Minero-Energético (uso no residencial)', 'V18': 'Protección/ Conservación ambiental (uso no residencial)', 'V19': 'En Construcción (uso no residencial)', 'V20': 'Sin información (uso no residencial)', 'V21': 'Viviendas', 'V22': 'Casa', 'V23': 'Apartamento', 'V24': 'Tipo cuarto', 'V25': 'Vivienda tradicional indígena', 'V26': 'Vivienda tradicional étnica (Afrocolombiana, Isleña, Rom)', 'V27': 'Otro (contenedor, carpa, embarcación, vagón, cueva, refugio natural, etc.)', 'V28': 'Ocupada con personas presentes', 'V29': 'Ocupada con todas las personas ausentes', 'V30': 'Vivienda temporal (para vacaciones, trabajo, etc.)', 'V31': 'Desocupada', 'V32': 'Hogares', 'V33': 'A', 'V34': 'B', 'V35': 'Estrato 1', 'V36': 'Estrato 2', 'V37': 'Estrato 3', 'V38': 'Estrato 4', 'V39': 'Estrato 5', 'V40': 'Estrato 6', 'V41': 'No sabe o no tiene estrato', 'V42': 'C', 'V43': 'D', 'V44': 'E', 'V45': 'F', 'V46': 'G', 'V47': 'H', 'V48': 'J', 'V49': 'K', 'V50': 'L', 'V51': 'M', 'V52': 'N', 'V53': 'O', 'V54': 'P', 'V55': 'Q', 'V56': 'Total personas', 'V57': 'Hombres', 'V58': 'Mujeres', 'V59': '0 a 9 años', 'V60': '10 a 19 años', 'V61': '20 a 29 años', 'V62': '30 a 39 años', 'V63': '40 a 49 años', 'V64': '50 a 59 años', 'V65': '60 a 69 años', 'V66': '70 a 79 años', 'V67': '80 años o más', 'V68': 'Ninguno (Educacion)', 'V69': 'Sin Información (Educacion)', 'V70': 'Preescolar - Prejardin, Básica primaria 1 (Educacion)', 'V71': 'Básica secundaria 6, Media tecnica 10, Normalista 10 (Educacion)', 'V72': 'Técnica profesional 1 año, Tecnológica 1 año, Universitario 1 año (Educacion)', 'V73': 'Especialización 1 año, Maestria 1 año, Doctorado 1 año (Educacion)'},inplace=True)
    except: df = pd.DataFrame()
    return df