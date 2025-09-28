#!/usr/bin/env python3
"""Script para testar e debugar o sistema de login do SparkOne."""

import requests
from bs4 import BeautifulSoup
import re

def test_login_flow():
    """Testa o fluxo completo de login."""
    base_url = "http://localhost:8000"
    
    print("🔍 Testando fluxo de login do SparkOne...")
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    # 1. Acessar página de login para obter CSRF token
    print("\n1. Obtendo página de login...")
    try:
        login_response = session.get(f"{base_url}/web/login")
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"   ❌ Erro ao acessar página de login: {login_response.status_code}")
            return False
            
        # Extrair CSRF token do HTML
        soup = BeautifulSoup(login_response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        
        if not csrf_input:
            print("   ❌ Token CSRF não encontrado no HTML")
            return False
            
        csrf_token = csrf_input.get('value')
        print(f"   ✅ Token CSRF obtido: {csrf_token[:20]}...")
        
        # Verificar se o cookie CSRF foi definido
        csrf_cookie = session.cookies.get('sparkone_csrftoken')
        if csrf_cookie:
            print(f"   ✅ Cookie CSRF definido: {csrf_cookie[:20]}...")
        else:
            print("   ⚠️  Cookie CSRF não foi definido")
            
    except Exception as e:
        print(f"   ❌ Erro ao obter página de login: {e}")
        return False
    
    # 2. Tentar fazer login
    print("\n2. Tentando fazer login...")
    try:
        login_data = {
            'username': 'user',
            'password': 'sparkone-dev',
            'csrf_token': csrf_token
        }
        
        login_post_response = session.post(
            f"{base_url}/web/login",
            data=login_data,
            allow_redirects=False  # Não seguir redirecionamentos automaticamente
        )
        
        print(f"   Status: {login_post_response.status_code}")
        print(f"   Headers: {dict(login_post_response.headers)}")
        
        if login_post_response.status_code == 302:
            print("   ✅ Login bem-sucedido (redirecionamento)")
            location = login_post_response.headers.get('location')
            print(f"   Redirecionando para: {location}")
            
            # Verificar se o cookie de sessão foi definido
            session_cookie = None
            for cookie in session.cookies:
                if cookie.name == 'sparkone_login_session':
                    session_cookie = cookie.value
                    break
                    
            if session_cookie:
                print(f"   ✅ Cookie de sessão definido: {session_cookie[:20]}...")
            else:
                print("   ❌ Cookie de sessão não foi definido")
                
        elif login_post_response.status_code == 400:
            print("   ❌ Erro 400 - Token CSRF inválido")
            soup = BeautifulSoup(login_post_response.text, 'html.parser')
            error_div = soup.find('div', class_='error-message')
            if error_div:
                print(f"   Mensagem de erro: {error_div.get_text().strip()}")
        elif login_post_response.status_code == 401:
            print("   ❌ Erro 401 - Credenciais inválidas")
            soup = BeautifulSoup(login_post_response.text, 'html.parser')
            error_div = soup.find('div', class_='error-message')
            if error_div:
                print(f"   Mensagem de erro: {error_div.get_text().strip()}")
        else:
            print(f"   ❌ Status inesperado: {login_post_response.status_code}")
            print(f"   Conteúdo: {login_post_response.text[:500]}...")
            
    except Exception as e:
        print(f"   ❌ Erro ao fazer login: {e}")
        return False
    
    # 3. Verificar se consegue acessar área protegida
    print("\n3. Testando acesso à área protegida...")
    try:
        app_response = session.get(f"{base_url}/web/app")
        print(f"   Status: {app_response.status_code}")
        
        if app_response.status_code == 200:
            print("   ✅ Acesso à área protegida bem-sucedido")
            return True
        else:
            print(f"   ❌ Não conseguiu acessar área protegida: {app_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao acessar área protegida: {e}")
        return False

def debug_csrf_validation():
    """Debug específico da validação CSRF."""
    print("\n🔧 Debug da validação CSRF...")
    
    session = requests.Session()
    base_url = "http://localhost:8000"
    
    # Obter página de login
    login_response = session.get(f"{base_url}/web/login")
    soup = BeautifulSoup(login_response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    csrf_token = csrf_input.get('value') if csrf_input else None
    
    print(f"Token CSRF do form: {csrf_token}")
    print(f"Cookie CSRF: {session.cookies.get('sparkone_csrftoken')}")
    print(f"Tokens são iguais: {csrf_token == session.cookies.get('sparkone_csrftoken')}")

if __name__ == "__main__":
    success = test_login_flow()
    debug_csrf_validation()
    
    if success:
        print("\n✅ Teste de login concluído com sucesso!")
    else:
        print("\n❌ Teste de login falhou!")