#!/usr/bin/env python3
"""
Script de debug para identificar problemas com elementos de áudio na interface SparkOne.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def setup_driver():
    """Configura o driver do Chrome com opções otimizadas."""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Permitir acesso ao microfone para testes
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--use-fake-device-for-media-stream")
    
    return webdriver.Chrome(options=options)


def login_to_sparkone(driver, base_url="http://localhost:8000"):
    """Faz login no SparkOne."""
    print("🔐 Fazendo login no SparkOne...")
    
    try:
        # Navegar para página de login
        driver.get(f"{base_url}/web/login")
        wait = WebDriverWait(driver, 15)
        
        print("   📄 Página de login carregada")
        print(f"   🌐 URL atual: {driver.current_url}")
        print(f"   📋 Título: {driver.title}")
        
        # Aguardar e preencher credenciais
        print("   👤 Preenchendo credenciais...")
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        
        username_field.clear()
        username_field.send_keys("admin")
        password_field.clear()
        password_field.send_keys("admin123")
        
        print("   ✅ Credenciais preenchidas")
        
        # Aguardar e clicar no botão de login
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        print("   🖱️ Clicando no botão de login...")
        login_button.click()
        
        # Aguardar redirecionamento com timeout maior
        print("   ⏳ Aguardando redirecionamento...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.url_contains("/web/app"))
        
        print("✅ Login realizado com sucesso!")
        print(f"   🌐 Nova URL: {driver.current_url}")
        return True
        
    except TimeoutException as e:
        print(f"❌ Timeout no login: {e}")
        print(f"   🌐 URL atual: {driver.current_url}")
        print(f"   📋 Título atual: {driver.title}")
        return False
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        print(f"   🌐 URL atual: {driver.current_url}")
        print(f"   📋 Título atual: {driver.title}")
        return False


def debug_audio_elements(driver):
    """Debug detalhado dos elementos de áudio."""
    print("\n🔍 INICIANDO DEBUG DOS ELEMENTOS DE ÁUDIO")
    print("=" * 50)
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # 1. Verificar se a página carregou completamente
        print("1️⃣ Verificando carregamento da página...")
        page_title = driver.title
        print(f"   Título da página: {page_title}")
        current_url = driver.current_url
        print(f"   URL atual: {current_url}")
        
        # 2. Listar todos os elementos com ID na página
        print("\n2️⃣ Listando todos os elementos com ID...")
        elements_with_id = driver.find_elements(By.CSS_SELECTOR, "[id]")
        print(f"   Total de elementos com ID: {len(elements_with_id)}")
        for element in elements_with_id:
            element_id = element.get_attribute("id")
            tag_name = element.tag_name
            print(f"   - {tag_name}#{element_id}")
        
        # 3. Verificar especificamente o botão de gravação
        print("\n3️⃣ Verificando botão de gravação...")
        try:
            record_button = driver.find_element(By.ID, "record-button")
            print("   ✅ Elemento #record-button encontrado!")
            print(f"   - Tag: {record_button.tag_name}")
            print(f"   - Texto: '{record_button.text}'")
            print(f"   - Visível: {record_button.is_displayed()}")
            print(f"   - Habilitado: {record_button.is_enabled()}")
            print(f"   - Classes CSS: {record_button.get_attribute('class')}")
            
            # Tentar clicar no botão
            print("\n   🖱️ Tentando clicar no botão...")
            if record_button.is_displayed() and record_button.is_enabled():
                record_button.click()
                print("   ✅ Clique realizado com sucesso!")
                time.sleep(2)
                
                # Verificar mudanças no botão após clique
                new_text = record_button.text
                new_classes = record_button.get_attribute('class')
                print(f"   - Novo texto: '{new_text}'")
                print(f"   - Novas classes: {new_classes}")
            else:
                print("   ❌ Botão não está visível ou habilitado")
                
        except NoSuchElementException:
            print("   ❌ Elemento #record-button NÃO encontrado!")
        
        # 4. Verificar elementos de preview de áudio
        print("\n4️⃣ Verificando elementos de preview de áudio...")
        try:
            audio_preview = driver.find_element(By.ID, "audio-preview")
            print("   ✅ Elemento #audio-preview encontrado!")
            print(f"   - Visível: {audio_preview.is_displayed()}")
            print(f"   - Hidden: {audio_preview.get_attribute('hidden')}")
            
            # Verificar elemento audio dentro do preview
            try:
                audio_element = audio_preview.find_element(By.TAG_NAME, "audio")
                print("   ✅ Elemento <audio> encontrado dentro do preview!")
                print(f"   - Src: {audio_element.get_attribute('src')}")
                print(f"   - Controls: {audio_element.get_attribute('controls')}")
            except NoSuchElementException:
                print("   ❌ Elemento <audio> NÃO encontrado dentro do preview!")
                
        except NoSuchElementException:
            print("   ❌ Elemento #audio-preview NÃO encontrado!")
        
        # 5. Verificar input de arquivo de áudio
        print("\n5️⃣ Verificando input de arquivo de áudio...")
        try:
            audio_input = driver.find_element(By.ID, "audio-file")
            print("   ✅ Elemento #audio-file encontrado!")
            print(f"   - Type: {audio_input.get_attribute('type')}")
            print(f"   - Accept: {audio_input.get_attribute('accept')}")
            print(f"   - Hidden: {audio_input.get_attribute('hidden')}")
        except NoSuchElementException:
            print("   ❌ Elemento #audio-file NÃO encontrado!")
        
        # 6. Verificar console do navegador
        print("\n6️⃣ Verificando logs do console...")
        logs = driver.get_log('browser')
        if logs:
            print(f"   Total de logs: {len(logs)}")
            for log in logs[-5:]:  # Últimos 5 logs
                print(f"   - [{log['level']}] {log['message']}")
        else:
            print("   Nenhum log encontrado no console")
        
        # 7. Verificar se JavaScript está funcionando
        print("\n7️⃣ Verificando JavaScript...")
        try:
            # Executar JavaScript simples para verificar se está funcionando
            result = driver.execute_script("return document.getElementById('record-button') !== null;")
            print(f"   JavaScript pode encontrar #record-button: {result}")
            
            # Verificar se as variáveis globais do app.js existem
            recording_state = driver.execute_script("return typeof recording !== 'undefined' ? recording : 'undefined';")
            print(f"   Variável 'recording': {recording_state}")
            
            media_recorder_state = driver.execute_script("return typeof mediaRecorder !== 'undefined' ? (mediaRecorder === null ? 'null' : 'exists') : 'undefined';")
            print(f"   Variável 'mediaRecorder': {media_recorder_state}")
            
        except Exception as e:
            print(f"   ❌ Erro ao executar JavaScript: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 DEBUG CONCLUÍDO")
        
    except Exception as e:
        print(f"❌ Erro durante debug: {e}")


def main():
    """Função principal."""
    driver = None
    
    try:
        print("🚀 Iniciando debug dos elementos de áudio...")
        
        # Configurar driver
        driver = setup_driver()
        
        # Fazer login
        if not login_to_sparkone(driver):
            return
        
        # Aguardar carregamento completo
        time.sleep(3)
        
        # Executar debug
        debug_audio_elements(driver)
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        if driver:
            print("\n🔒 Fechando navegador...")
            driver.quit()


if __name__ == "__main__":
    main()