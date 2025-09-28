#!/usr/bin/env python3
"""
Script para debugar o problema de CSRF no login do SparkOne.
"""

import requests
from bs4 import BeautifulSoup
import re

def main():
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    print("🔍 Debug detalhado do problema CSRF...")
    
    # 1. Acessar /web/app (que deve redirecionar para login)
    print("\n1. Acessando /web/app...")
    response = session.get(f"{base_url}/web/app")
    print(f"   Status: {response.status_code}")
    
    # Extrair CSRF token do formulário
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    csrf_token = csrf_input['value'] if csrf_input else None
    
    print(f"   CSRF Token do form: {csrf_token}")
    print(f"   Cookies após GET: {dict(session.cookies)}")
    
    # 2. Tentar fazer login com as credenciais corretas
    print("\n2. Tentando login com debug...")
    login_data = {
        'username': 'user',
        'password': 'sparkone-dev',  # Senha correta do .env.example
        'csrf_token': csrf_token
    }
    
    login_response = session.post(
        f"{base_url}/web/login",
        data=login_data,
        allow_redirects=False
    )
    
    print(f"   Status: {login_response.status_code}")
    print(f"   Cookies após POST: {dict(session.cookies)}")
    
    if login_response.status_code == 302:
        print("   ✅ Login bem-sucedido!")
        print(f"   Location: {login_response.headers.get('location')}")
        
        # Verificar se o cookie de sessão foi definido
        session_cookie = session.cookies.get('sparkone_login_session')
        if session_cookie:
            print(f"   ✅ Cookie de sessão: {session_cookie[:20]}...")
        else:
            print("   ❌ Cookie de sessão não foi definido")
            
    elif login_response.status_code == 401:
        print("   ❌ Credenciais incorretas")
        print(f"   Response: {login_response.text[:200]}...")
    else:
        print(f"   ❌ Erro inesperado: {login_response.status_code}")
        print(f"   Response: {login_response.text[:200]}...")
    
    # 3. Testar abordagem alternativa - obter token diretamente do /web/login
    print("\n3. Tentando abordagem alternativa...")
    session2 = requests.Session()
    
    login_page_response = session2.get(f"{base_url}/web/login")
    soup2 = BeautifulSoup(login_page_response.text, 'html.parser')
    csrf_input2 = soup2.find('input', {'name': 'csrf_token'})
    csrf_token2 = csrf_input2['value'] if csrf_input2 else None
    
    print(f"   CSRF Token direto do /web/login: {csrf_token2}")
    print(f"   Cookies após GET /web/login: {dict(session2.cookies)}")
    
    login_data2 = {
        'username': 'user',
        'password': 'sparkone-dev',  # Senha correta
        'csrf_token': csrf_token2
    }
    
    login_response2 = session2.post(
        f"{base_url}/web/login",
        data=login_data2,
        allow_redirects=False
    )
    
    print(f"   Status com token direto: {login_response2.status_code}")
    
    if login_response2.status_code == 302:
        print("   ✅ Login bem-sucedido com token direto!")
        print(f"   Location: {login_response2.headers.get('location')}")
        
        # Verificar se o cookie de sessão foi definido
        session_cookie2 = session2.cookies.get('sparkone_login_session')
        if session_cookie2:
            print(f"   ✅ Cookie de sessão: {session_cookie2[:20]}...")
            
            # Testar acesso à página protegida
            print("\n4. Testando acesso à página protegida...")
            protected_response = session2.get(f"{base_url}/web/app")
            print(f"   Status /web/app: {protected_response.status_code}")
            
            if protected_response.status_code == 200:
                print("   ✅ Acesso à página protegida bem-sucedido!")
                if "Envie texto, voz ou imagens" in protected_response.text:
                    print("   ✅ Página carregou corretamente!")
                else:
                    print("   ⚠️ Página carregou mas conteúdo inesperado")
            else:
                print("   ❌ Falha no acesso à página protegida")
        else:
            print("   ❌ Cookie de sessão não foi definido")
    else:
        print(f"   ❌ Falha no login: {login_response2.status_code}")
        print(f"   Response: {login_response2.text[:200]}...")

if __name__ == "__main__":
    main()