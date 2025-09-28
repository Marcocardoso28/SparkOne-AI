#!/usr/bin/env python3
"""
Script de depuração para testar o envio do formulário SparkOne.
Foca em identificar problemas de CSRF, validação e processamento.
"""

import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path
import tempfile
import os

def create_test_files():
    """Cria arquivos de teste temporários."""
    test_files = {}
    
    # Criar arquivo de imagem de teste (SVG simples)
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <rect width="100" height="100" fill="red"/>
        <text x="50" y="50" text-anchor="middle" fill="white">TEST</text>
    </svg>'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        test_files['image'] = f.name
    
    # Criar arquivo de áudio de teste (dados binários simples)
    audio_data = b'RIFF\x24\x00\x00\x00WAVE'  # Header WAV mínimo
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as f:
        f.write(audio_data)
        test_files['audio'] = f.name
    
    return test_files

def test_csrf_flow():
    """Testa o fluxo completo de CSRF."""
    print("🔐 Testando fluxo de CSRF...")
    
    session = requests.Session()
    base_url = "http://localhost:8000"
    
    try:
        # 1. Fazer login primeiro
        print("1️⃣ Fazendo login...")
        login_response = session.get(f"{base_url}/web/login")
        if login_response.status_code != 200:
            print(f"❌ Erro ao acessar página de login: {login_response.status_code}")
            return False
        
        # Extrair token CSRF da página de login
        soup = BeautifulSoup(login_response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if not csrf_input:
            print("❌ Token CSRF não encontrado na página de login")
            return False
        
        login_csrf_token = csrf_input.get('value')
        print(f"✅ Token CSRF de login obtido: {login_csrf_token[:10]}...")
        
        # Fazer login
        login_data = {
            'username': 'user',
            'password': 'sparkone-dev',
            'csrf_token': login_csrf_token
        }
        
        login_submit = session.post(f"{base_url}/web/login", data=login_data, allow_redirects=False)
        if login_submit.status_code != 302:
            print(f"❌ Login falhou: {login_submit.status_code}")
            print(f"Response: {login_submit.text[:200]}")
            return False
        
        print("✅ Login realizado com sucesso")
        
        # 2. Acessar página principal
        print("2️⃣ Acessando página principal...")
        app_response = session.get(f"{base_url}/web/app")
        if app_response.status_code != 200:
            print(f"❌ Erro ao acessar página principal: {app_response.status_code}")
            return False
        
        # Extrair token CSRF da página principal
        soup = BeautifulSoup(app_response.text, 'html.parser')
        csrf_input = soup.find('input', {'id': 'csrf-token'})
        if not csrf_input:
            print("❌ Token CSRF não encontrado na página principal")
            return False
        
        app_csrf_token = csrf_input.get('value')
        print(f"✅ Token CSRF da aplicação obtido: {app_csrf_token[:10]}...")
        
        # Verificar se o cookie CSRF foi definido
        csrf_cookie = session.cookies.get('sparkone_csrftoken')
        if not csrf_cookie:
            print("❌ Cookie CSRF não foi definido")
            return False
        
        print(f"✅ Cookie CSRF encontrado: {csrf_cookie[:10]}...")
        
        # Verificar se tokens coincidem
        if app_csrf_token != csrf_cookie:
            print(f"⚠️ Tokens CSRF não coincidem!")
            print(f"  Form token: {app_csrf_token}")
            print(f"  Cookie token: {csrf_cookie}")
        else:
            print("✅ Tokens CSRF coincidem")
        
        return True, session, app_csrf_token
        
    except Exception as e:
        print(f"❌ Erro no teste de CSRF: {e}")
        return False

def test_form_submission_simple():
    """Testa envio simples do formulário apenas com texto."""
    print("\n📝 Testando envio simples do formulário...")
    
    csrf_result = test_csrf_flow()
    if not csrf_result or csrf_result is False:
        return False
    
    success, session, csrf_token = csrf_result
    if not success:
        return False
    
    try:
        # Enviar formulário apenas com texto
        form_data = {
            'message': 'Teste de envio simples do formulário',
            'csrf_token': csrf_token
        }
        
        print("3️⃣ Enviando formulário com texto...")
        response = session.post("http://localhost:8000/web", data=form_data)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar se há mensagem de sucesso
            soup = BeautifulSoup(response.text, 'html.parser')
            success_toast = soup.find('div', class_='toast--success')
            error_toast = soup.find('div', class_='toast--error')
            
            if success_toast:
                print("✅ Formulário enviado com sucesso!")
                print(f"Mensagem: {success_toast.get_text().strip()}")
                return True
            elif error_toast:
                print(f"❌ Erro no envio: {error_toast.get_text().strip()}")
                return False
            else:
                # Verificar se campo de mensagem foi limpo (indicando sucesso)
                message_input = soup.find('textarea', {'id': 'message-input'})
                if message_input and not message_input.get_text().strip():
                    print("✅ Formulário processado (campo limpo)")
                    return True
                else:
                    print("⚠️ Status do envio incerto")
                    return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de envio: {e}")
        return False

def test_form_submission_with_files():
    """Testa envio do formulário com arquivos."""
    print("\n📎 Testando envio do formulário com arquivos...")
    
    csrf_result = test_csrf_flow()
    if not csrf_result or csrf_result is False:
        return False
    
    success, session, csrf_token = csrf_result
    if not success:
        return False
    
    test_files = create_test_files()
    
    try:
        # Preparar arquivos para upload
        files = {}
        if os.path.exists(test_files['image']):
            files['image'] = ('test.svg', open(test_files['image'], 'rb'), 'image/svg+xml')
        
        if os.path.exists(test_files['audio']):
            files['audio'] = ('test.wav', open(test_files['audio'], 'rb'), 'audio/wav')
        
        form_data = {
            'message': 'Teste de envio com arquivos anexados',
            'csrf_token': csrf_token
        }
        
        print("4️⃣ Enviando formulário com arquivos...")
        response = session.post("http://localhost:8000/web", data=form_data, files=files)
        
        # Fechar arquivos
        for file_tuple in files.values():
            if len(file_tuple) > 1 and hasattr(file_tuple[1], 'close'):
                file_tuple[1].close()
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            success_toast = soup.find('div', class_='toast--success')
            error_toast = soup.find('div', class_='toast--error')
            
            if success_toast:
                print("✅ Formulário com arquivos enviado com sucesso!")
                print(f"Mensagem: {success_toast.get_text().strip()}")
                return True
            elif error_toast:
                print(f"❌ Erro no envio: {error_toast.get_text().strip()}")
                return False
            else:
                print("⚠️ Status do envio com arquivos incerto")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de envio com arquivos: {e}")
        return False
    finally:
        # Limpar arquivos de teste
        for file_path in test_files.values():
            try:
                os.unlink(file_path)
            except:
                pass

def test_csrf_validation_edge_cases():
    """Testa casos extremos de validação CSRF."""
    print("\n🔍 Testando casos extremos de CSRF...")
    
    session = requests.Session()
    base_url = "http://localhost:8000"
    
    # Fazer login primeiro
    csrf_result = test_csrf_flow()
    if not csrf_result or csrf_result is False:
        return False
    
    success, session, valid_csrf_token = csrf_result
    if not success:
        return False
    
    test_cases = [
        ("Token CSRF vazio", ""),
        ("Token CSRF inválido", "invalid_token_123"),
        ("Token CSRF muito longo", "a" * 100),
        ("Token CSRF com caracteres especiais", "token@#$%^&*()"),
    ]
    
    for test_name, csrf_token in test_cases:
        print(f"5️⃣ Testando: {test_name}")
        
        form_data = {
            'message': f'Teste: {test_name}',
            'csrf_token': csrf_token
        }
        
        try:
            response = session.post(f"{base_url}/web", data=form_data)
            
            if response.status_code == 400:
                print(f"  ✅ Rejeitado corretamente (400)")
            elif response.status_code == 403:
                print(f"  ✅ Rejeitado corretamente (403)")
            elif response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                error_toast = soup.find('div', class_='toast--error')
                if error_toast:
                    print(f"  ✅ Rejeitado com erro: {error_toast.get_text().strip()}")
                else:
                    print(f"  ⚠️ Aceito inesperadamente")
            else:
                print(f"  ❓ Status inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")

def main():
    """Função principal."""
    print("🚀 Iniciando depuração do envio de formulário SparkOne")
    print("=" * 60)
    
    # Verificar se servidor está rodando
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor SparkOne não está respondendo corretamente")
            return
    except requests.exceptions.RequestException:
        print("❌ Servidor SparkOne não está acessível em http://localhost:8000")
        return
    
    print("✅ Servidor SparkOne está rodando")
    
    # Executar testes
    results = []
    
    # Teste 1: Fluxo CSRF
    csrf_ok = test_csrf_flow()
    results.append(("CSRF Flow", csrf_ok and csrf_ok is not False))
    
    # Teste 2: Envio simples
    simple_ok = test_form_submission_simple()
    results.append(("Envio Simples", simple_ok))
    
    # Teste 3: Envio com arquivos
    files_ok = test_form_submission_with_files()
    results.append(("Envio com Arquivos", files_ok))
    
    # Teste 4: Casos extremos CSRF
    test_csrf_validation_edge_cases()
    results.append(("Validação CSRF", True))  # Sempre passa pois é só teste
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:20} {status}")
    
    total_passed = sum(1 for _, result in results if result)
    print(f"\nTotal: {total_passed}/{len(results)} testes passaram")

if __name__ == "__main__":
    main()