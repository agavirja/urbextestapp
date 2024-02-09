import streamlit as st

st.set_page_config(layout='wide')

# streamlit run D:\Dropbox\Empresa\Empresa_Data\_APP\Home.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Empresa_Data\_APP"

#------------#
# Powersheel #

# Archivos donde esta la palabra "urbextestapp\.streamlit\.app" o "urbextestapp\.streamlit\.app"
# Get-ChildItem -Path D:\Dropbox\Empresa\Empresa_Data\_APP -Recurse -Filter *.py | ForEach-Object { if (Get-Content $_.FullName | Select-String -Pattern 'localhost:8501' -Quiet) { $_.FullName } }

# Reemplazar "urbextestapp.streamlit.app" por "localhost:8501" o al reves en los archivos donde esta la palabra
# Get-ChildItem -Path D:\Dropbox\Empresa\Empresa_Data\_APP -Recurse -Filter *.py | ForEach-Object {(Get-Content $_.FullName) | ForEach-Object {$_ -replace 'localhost:8501', 'urbextestapp.streamlit.app'} | Set-Content $_.FullName}
