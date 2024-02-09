import streamlit as st

st.set_page_config(layout='wide')

# streamlit run D:\Dropbox\Empresa\Empresa_Data\_APP\Home.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Empresa_Data\_APP"

#------------#
# Powersheel #

# Archivos donde esta la palabra "urbextestapp\.streamlit\.app" o "urbextestapp\.streamlit\.app"

# opcion 1
# Get-ChildItem -Path D:\Dropbox\Empresa\Empresa_Data\_APP -Recurse -Filter *.py | ForEach-Object { if (Get-Content $_.FullName | Select-String -Pattern 'urbextestapp\.streamlit\.app' -Quiet) { $_.FullName } }

# opcion 2
# Get-ChildItem -Path D:\Dropbox\Empresa\Empresa_Data\_APP -Recurse -Filter *.py | ForEach-Object { if (Get-Content $_.FullName | Select-String -Pattern 'urbextestapp\.streamlit\.app' -Quiet) { $_.FullName } }

# opcion 3
# Get-ChildItem -Path D:\Dropbox\Empresa\Empresa_Data\_APP -Recurse -Filter *.py | ForEach-Object { if (Get-Content $_.FullName | Select-String -Pattern 'localhost' -Quiet) { $_.FullName } }


# Reemplazar "urbextestapp\.streamlit\.app" por "urbextestapp\.streamlit\.app" o al reves en los archivos donde esta la palabra

#Get-ChildItem -Path D:\Dropbox\Empresa\Empresa_Data\_APP -Recurse -Filter *.py | ForEach-Object {
#    (Get-Content $_.FullName) | ForEach-Object {
#        $_ -replace 'urbextestapp\.streamlit\.app', 'urbextestapp\.streamlit\.app'
#    } | Set-Content $_.FullName
#}
