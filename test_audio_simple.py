#!/usr/bin/env python3
"""
Script simplificado para testar elementos de áudio no SparkOne.
"""

import requests
from bs4 import BeautifulSoup
import re

def test_audio_elements():
    """Testa se os elementos de áudio estão presentes no HTML."""
    print("🎵 Testando elementos de áudio no SparkOne...")
    
    session = requests.Session()
    base_url = "http://localhost:8000"
    
    # 1. Fazer login
    print("\n1. Fazendo login...")
    login_response = session.get(f"{base_url}/web/login")
    soup = BeautifulSoup(login_response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    csrf_token = csrf_input['value'] if csrf_input else None
    
    login_data = {
        'username': 'user',
        'password': 'sparkone-dev',
        'csrf_token': csrf_token
    }
    
    login_post = session.post(f"{base_url}/web/login", data=login_data, allow_redirects=False)
    
    if login_post.status_code != 302:
        print(f"   ❌ Falha no login: {login_post.status_code}")
        return False
    
    print("   ✅ Login bem-sucedido")
    
    # 2. Acessar página principal
    print("\n2. Acessando página principal...")
    app_response = session.get(f"{base_url}/web/app")
    
    if app_response.status_code != 200:
        print(f"   ❌ Falha ao acessar /web/app: {app_response.status_code}")
        return False
    
    print("   ✅ Página principal carregada")
    
    # 3. Analisar HTML para elementos de áudio
    print("\n3. Analisando elementos de áudio...")
    soup = BeautifulSoup(app_response.text, 'html.parser')
    
    # Verificar botão de gravação
    record_button = soup.find('button', {'id': 'record-button'})
    if record_button:
        print("   ✅ Botão de gravação (#record-button) encontrado")
        print(f"      Texto: {record_button.get_text().strip()}")
        print(f"      Classes: {record_button.get('class', [])}")
    else:
        print("   ❌ Botão de gravação (#record-button) NÃO encontrado")
    
    # Verificar input de arquivo de áudio
    audio_input = soup.find('input', {'id': 'audio-file'})
    if audio_input:
        print("   ✅ Input de arquivo de áudio (#audio-file) encontrado")
        print(f"      Tipo: {audio_input.get('type')}")
        print(f"      Accept: {audio_input.get('accept')}")
    else:
        print("   ❌ Input de arquivo de áudio (#audio-file) NÃO encontrado")
    
    # Verificar área de preview de áudio
    audio_preview = soup.find('div', {'id': 'audio-preview'})
    if audio_preview:
        print("   ✅ Área de preview de áudio (#audio-preview) encontrada")
    else:
        print("   ❌ Área de preview de áudio (#audio-preview) NÃO encontrada")
    
    # Verificar se há elementos audio
    audio_elements = soup.find_all('audio')
    print(f"   📊 Elementos <audio> encontrados: {len(audio_elements)}")
    
    # 4. Verificar JavaScript
    print("\n4. Verificando JavaScript...")
    script_tags = soup.find_all('script', src=True)
    app_js_found = False
    
    for script in script_tags:
        src = script.get('src', '')
        if 'app.js' in src:
            app_js_found = True
            print(f"   ✅ app.js encontrado: {src}")
            break
    
    if not app_js_found:
        print("   ❌ app.js NÃO encontrado")
    
    # 5. Procurar por padrões relacionados a áudio no HTML
    print("\n5. Procurando padrões de áudio no HTML...")
    html_content = app_response.text.lower()
    
    audio_patterns = [
        'record',
        'audio',
        'microphone',
        'mediarecorder',
        'getusermedia'
    ]
    
    for pattern in audio_patterns:
        if pattern in html_content:
            print(f"   ✅ Padrão '{pattern}' encontrado no HTML")
        else:
            print(f"   ❌ Padrão '{pattern}' NÃO encontrado no HTML")
    
    return True

def main():
    """Função principal."""
    try:
        test_audio_elements()
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()