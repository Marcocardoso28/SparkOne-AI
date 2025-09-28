#!/usr/bin/env python3
"""
Script para testar todas as funcionalidades da interface de chat do SparkOne
usando Selenium WebDriver.
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

def setup_driver():
    """Configura o driver do Chrome com opções otimizadas."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")
    # Remover --headless para ver o navegador em ação
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def login_to_app(driver):
    """Realiza o login na aplicação."""
    print("🔐 Realizando login...")
    
    try:
        # Navegar para a página de login
        print("📍 Navegando para página de login...")
        driver.get("http://localhost:8000/web/login")
        time.sleep(3)
        
        print("🔍 Procurando campos de login...")
        # Aguardar campos aparecerem
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Preencher credenciais
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        print("✏️ Preenchendo credenciais...")
        username_field.clear()
        username_field.send_keys("user")
        password_field.clear()
        password_field.send_keys("sparkone-dev")
        
        # Clicar no botão de login
        print("🔘 Clicando no botão de login...")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Aguardar redirecionamento
        print("⏳ Aguardando redirecionamento...")
        WebDriverWait(driver, 15).until(
            EC.url_contains("/web/app")
        )
        
        print("✅ Login realizado com sucesso!")
        return True
        
    except TimeoutException as e:
        print(f"⏰ Timeout durante login: {e}")
        print(f"🌐 URL atual: {driver.current_url}")
        return False
    except NoSuchElementException as e:
        print(f"🔍 Elemento não encontrado: {e}")
        print("📄 HTML da página:")
        print(driver.page_source[:500] + "...")
        return False
    except Exception as e:
        print(f"❌ Erro durante login: {e}")
        print(f"🌐 URL atual: {driver.current_url}")
        return False

def test_page_load(driver):
    """Testa se a página principal carrega corretamente."""
    print("\n📄 Testando carregamento da página...")
    
    try:
        # Verificar se estamos na página correta
        current_url = driver.current_url
        assert "/web/app" in current_url, f"URL incorreta: {current_url}"
        
        # Verificar título da página
        title = driver.title
        print(f"📋 Título da página: {title}")
        
        # Aguardar elementos principais carregarem
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ Página carregada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no carregamento da página: {e}")
        return False

def test_chat_interface_elements(driver):
    """Testa se os elementos da interface de chat estão presentes."""
    print("\n🎨 Testando elementos da interface...")
    
    elements_to_check = [
        ("Campo de entrada de texto", "input[type='text'], textarea, [contenteditable]"),
        ("Botão de envio", "button[type='submit'], button:contains('Enviar'), .send-button"),
        ("Área de mensagens", ".messages, .chat-messages, .conversation"),
        ("Botão de upload", "input[type='file'], .upload-button, .file-input"),
    ]
    
    found_elements = []
    
    for name, selector in elements_to_check:
        try:
            # Tentar diferentes seletores
            selectors = selector.split(", ")
            element_found = False
            
            for sel in selectors:
                try:
                    if ":contains(" in sel:
                        # Para seletores com :contains, usar XPath
                        text = sel.split(":contains('")[1].split("')")[0]
                        xpath_selector = f"//*[contains(text(), '{text}')]"
                        elements = driver.find_elements(By.XPATH, xpath_selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    
                    if elements:
                        found_elements.append((name, sel, len(elements)))
                        element_found = True
                        break
                except:
                    continue
            
            if element_found:
                print(f"✅ {name}: Encontrado")
            else:
                print(f"⚠️  {name}: Não encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao verificar {name}: {e}")
    
    return found_elements

def test_text_input(driver):
    """Testa a funcionalidade de entrada de texto."""
    print("\n💬 Testando entrada de texto...")
    
    try:
        # Procurar campo de entrada de texto
        text_inputs = driver.find_elements(By.CSS_SELECTOR, 
            "input[type='text'], textarea, [contenteditable='true']")
        
        if not text_inputs:
            print("⚠️  Campo de entrada de texto não encontrado")
            return False
        
        # Usar o primeiro campo encontrado
        text_input = text_inputs[0]
        
        # Testar digitação
        test_message = "Olá! Este é um teste da funcionalidade de chat."
        text_input.clear()
        text_input.send_keys(test_message)
        
        # Verificar se o texto foi inserido
        if text_input.get_attribute("value") == test_message or text_input.text == test_message:
            print("✅ Texto inserido com sucesso!")
            
            # Tentar enviar a mensagem
            try:
                # Procurar botão de envio
                send_buttons = driver.find_elements(By.CSS_SELECTOR, 
                    "button[type='submit'], .send-button, button:contains('Enviar')")
                
                if send_buttons:
                    send_buttons[0].click()
                    print("✅ Mensagem enviada!")
                    time.sleep(2)  # Aguardar processamento
                else:
                    # Tentar Enter
                    text_input.send_keys(Keys.RETURN)
                    print("✅ Mensagem enviada com Enter!")
                    time.sleep(2)
                
                return True
                
            except Exception as e:
                print(f"⚠️  Erro ao enviar mensagem: {e}")
                return False
        else:
            print("❌ Falha ao inserir texto")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de entrada de texto: {e}")
        return False

def test_file_upload(driver):
    """Testa a funcionalidade de upload de arquivos."""
    print("\n📎 Testando upload de arquivos...")
    
    try:
        # Procurar input de arquivo
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        
        if not file_inputs:
            print("⚠️  Campo de upload não encontrado")
            return False
        
        # Criar um arquivo de teste temporário
        test_file_path = os.path.join(os.getcwd(), "test_image.txt")
        with open(test_file_path, "w") as f:
            f.write("Este é um arquivo de teste para upload.")
        
        try:
            # Fazer upload do arquivo
            file_input = file_inputs[0]
            file_input.send_keys(test_file_path)
            
            print("✅ Arquivo selecionado para upload!")
            time.sleep(2)
            
            # Limpar arquivo de teste
            os.remove(test_file_path)
            
            return True
            
        except Exception as e:
            # Limpar arquivo de teste em caso de erro
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            print(f"❌ Erro no upload: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de upload: {e}")
        return False

def test_ui_responsiveness(driver):
    """Testa a responsividade da interface."""
    print("\n📱 Testando responsividade...")
    
    # Tamanhos de tela para testar
    screen_sizes = [
        (1920, 1080, "Desktop Grande"),
        (1280, 720, "Desktop Padrão"),
        (768, 1024, "Tablet"),
        (375, 667, "Mobile")
    ]
    
    for width, height, device in screen_sizes:
        try:
            driver.set_window_size(width, height)
            time.sleep(1)
            
            # Verificar se a página ainda está acessível
            body = driver.find_element(By.TAG_NAME, "body")
            if body:
                print(f"✅ {device} ({width}x{height}): OK")
            else:
                print(f"❌ {device} ({width}x{height}): Problema")
                
        except Exception as e:
            print(f"❌ {device} ({width}x{height}): Erro - {e}")
    
    # Restaurar tamanho padrão
    driver.set_window_size(1280, 720)
    return True

def capture_page_info(driver):
    """Captura informações gerais da página."""
    print("\n📊 Informações da página:")
    
    try:
        print(f"🌐 URL atual: {driver.current_url}")
        print(f"📋 Título: {driver.title}")
        
        # Contar elementos
        all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
        inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea, [contenteditable]")
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        
        print(f"🔢 Total de elementos: {len(all_elements)}")
        print(f"📝 Campos de entrada: {len(inputs)}")
        print(f"🔘 Botões: {len(buttons)}")
        
        # Capturar screenshot
        screenshot_path = "chat_interface_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot salvo: {screenshot_path}")
        
    except Exception as e:
        print(f"❌ Erro ao capturar informações: {e}")

def main():
    """Função principal que executa todos os testes."""
    print("🚀 Iniciando testes da interface de chat do SparkOne...")
    
    driver = None
    try:
        # Configurar driver
        driver = setup_driver()
        
        # Realizar login
        if not login_to_app(driver):
            print("❌ Falha no login. Abortando testes.")
            return
        
        # Executar testes
        test_page_load(driver)
        test_chat_interface_elements(driver)
        test_text_input(driver)
        test_file_upload(driver)
        test_ui_responsiveness(driver)
        capture_page_info(driver)
        
        print("\n🎉 Testes concluídos!")
        print("⏳ Aguardando 10 segundos para visualização...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("🔚 Navegador fechado.")

if __name__ == "__main__":
    main()