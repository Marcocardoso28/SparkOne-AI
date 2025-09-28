#!/usr/bin/env python3
"""
Script para testar o login via navegador usando selenium como alternativa.
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def test_with_requests():
    """Teste usando requests (já sabemos que funciona)."""
    print("🔍 Testando login com requests...")
    
    session = requests.Session()
    
    # Obter token CSRF
    response = session.get("http://localhost:8000/web/login")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    csrf_token = csrf_input['value'] if csrf_input else None
    
    # Fazer login
    login_data = {
        'username': 'user',
        'password': 'sparkone-dev',
        'csrf_token': csrf_token
    }
    
    login_response = session.post(
        "http://localhost:8000/web/login",
        data=login_data,
        allow_redirects=False
    )
    
    if login_response.status_code == 302:
        print("   ✅ Login via requests: SUCESSO")
        return True
    else:
        print(f"   ❌ Login via requests: FALHOU ({login_response.status_code})")
        return False

def test_with_selenium():
    """Teste usando selenium."""
    print("\n🌐 Testando login com Selenium...")
    
    try:
        # Configurar Chrome
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,720")
        
        # Tentar inicializar o driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            print(f"   ❌ Erro ao inicializar Chrome: {e}")
            print("   💡 Certifique-se de que o ChromeDriver está instalado")
            return False
        
        try:
            # Navegar para a página de login
            print("   📍 Navegando para http://localhost:8000/web/login")
            driver.get("http://localhost:8000/web/login")
            
            # Aguardar a página carregar
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            
            # Preencher credenciais
            print("   ✏️ Preenchendo credenciais...")
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys("user")
            
            password_field.clear()
            password_field.send_keys("sparkone-dev")
            
            # Clicar no botão de login
            print("   🔘 Clicando no botão de login...")
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Aguardar redirecionamento ou mensagem de erro
            time.sleep(2)
            
            current_url = driver.current_url
            print(f"   📍 URL atual: {current_url}")
            
            if "/web/app" in current_url:
                print("   ✅ Login via Selenium: SUCESSO - Redirecionado para /web/app")
                
                # Verificar se a página carregou corretamente
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    page_title = driver.title
                    print(f"   📄 Título da página: {page_title}")
                    
                    # Verificar se há elementos esperados na página
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    if "SparkOne" in body_text:
                        print("   ✅ Página carregou com conteúdo esperado")
                    else:
                        print("   ⚠️ Página carregou mas conteúdo pode estar incompleto")
                        
                except TimeoutException:
                    print("   ⚠️ Timeout ao aguardar carregamento da página")
                
                return True
            else:
                # Verificar se há mensagem de erro
                try:
                    error_element = driver.find_element(By.CLASS_NAME, "error-message")
                    error_text = error_element.text
                    print(f"   ❌ Login via Selenium: FALHOU - {error_text}")
                except:
                    print("   ❌ Login via Selenium: FALHOU - Não redirecionou")
                
                return False
                
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"   ❌ Erro no teste Selenium: {e}")
        return False

def main():
    print("🧪 Teste Completo de Login - SparkOne")
    print("=" * 50)
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get("http://localhost:8000/web/login", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor não está respondendo corretamente")
            return
    except requests.exceptions.RequestException:
        print("❌ Servidor não está rodando em http://localhost:8000")
        return
    
    print("✅ Servidor está rodando")
    
    # Teste 1: Requests (já sabemos que funciona)
    requests_success = test_with_requests()
    
    # Teste 2: Selenium (teste real do navegador)
    selenium_success = test_with_selenium()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print(f"   Requests: {'✅ PASSOU' if requests_success else '❌ FALHOU'}")
    print(f"   Selenium: {'✅ PASSOU' if selenium_success else '❌ FALHOU'}")
    
    if requests_success and selenium_success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   O login está funcionando corretamente tanto via API quanto via navegador.")
    elif requests_success:
        print("\n⚠️ Login funciona via API mas pode ter problemas no navegador.")
        print("   Verifique se o ChromeDriver está instalado para testes completos.")
    else:
        print("\n❌ Problemas detectados no sistema de login.")

if __name__ == "__main__":
    main()