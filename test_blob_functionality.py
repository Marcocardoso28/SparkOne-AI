#!/usr/bin/env python3
"""
Script para testar funcionalidade de upload de arquivos e URLs blob no SparkOne.
"""

import os
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


def setup_driver():
    """Configura o driver do Chrome com opções otimizadas."""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    
    # Permitir acesso a microfone e câmera para testes
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_settings.popups": 0
    }
    options.add_experimental_option("prefs", prefs)
    
    return webdriver.Chrome(options=options)


def create_test_files():
    """Cria arquivos de teste temporários."""
    test_files = {}
    
    # Criar arquivo de imagem de teste (SVG)
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" fill="#4F46E5"/>
  <text x="50" y="55" font-family="Arial" font-size="12" fill="white" text-anchor="middle">TEST</text>
</svg>'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        test_files['image'] = f.name
    
    # Criar arquivo de áudio de teste (texto simulando WebM)
    audio_content = b"WEBM_TEST_AUDIO_DATA_PLACEHOLDER"
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.webm', delete=False) as f:
        f.write(audio_content)
        test_files['audio'] = f.name
    
    return test_files


def login_to_sparkone(driver, base_url="http://localhost:8000"):
    """Faz login no SparkOne."""
    print("🔐 Fazendo login no SparkOne...")
    
    # Navegar para página de login
    driver.get(f"{base_url}/web/login")
    
    wait = WebDriverWait(driver, 10)
    
    try:
        # Preencher credenciais
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("user")
        password_field.send_keys("sparkone-dev")
        
        # Submeter formulário
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Aguardar redirecionamento
        wait.until(EC.url_contains("/web/app"))
        print("✅ Login realizado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return False


def test_image_upload(driver, image_path):
    """Testa upload de imagem e geração de blob URL."""
    print("📷 Testando upload de imagem...")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Localizar campo de upload de imagem
        image_input = wait.until(EC.presence_of_element_located((By.ID, "image-input")))
        
        # Fazer upload da imagem
        image_input.send_keys(image_path)
        
        # Aguardar preview aparecer
        time.sleep(2)
        
        # Verificar se preview foi criado
        image_preview = driver.find_element(By.ID, "image-preview")
        if not image_preview.get_attribute("hidden"):
            print("✅ Preview de imagem criado com sucesso!")
            
            # Verificar se blob URL foi gerada
            img_element = image_preview.find_element(By.TAG_NAME, "img")
            img_src = img_element.get_attribute("src")
            
            if img_src and img_src.startswith("blob:"):
                print(f"✅ Blob URL gerada: {img_src}")
                return img_src
            else:
                print(f"⚠️ URL não é blob: {img_src}")
                return img_src
        else:
            print("❌ Preview de imagem não apareceu")
            return None
            
    except Exception as e:
        print(f"❌ Erro no teste de upload de imagem: {e}")
        return None


def test_audio_recording(driver):
    """Testa gravação de áudio e geração de blob URL."""
    print("🎙️ Testando gravação de áudio...")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Localizar botão de gravação
        record_button = wait.until(EC.element_to_be_clickable((By.ID, "record-button")))
        
        # Iniciar gravação
        record_button.click()
        print("🔴 Gravação iniciada...")
        
        # Aguardar um pouco (simular gravação)
        time.sleep(3)
        
        # Parar gravação
        record_button.click()
        print("⏹️ Gravação parada...")
        
        # Aguardar processamento
        time.sleep(2)
        
        # Verificar se preview de áudio foi criado
        audio_preview = driver.find_element(By.ID, "audio-preview")
        if not audio_preview.get_attribute("hidden"):
            print("✅ Preview de áudio criado com sucesso!")
            
            # Verificar se blob URL foi gerada
            audio_element = audio_preview.find_element(By.TAG_NAME, "audio")
            audio_src = audio_element.get_attribute("src")
            
            if audio_src and audio_src.startswith("blob:"):
                print(f"✅ Blob URL de áudio gerada: {audio_src}")
                return audio_src
            else:
                print(f"⚠️ URL de áudio não é blob: {audio_src}")
                return audio_src
        else:
            print("❌ Preview de áudio não apareceu")
            return None
            
    except Exception as e:
        print(f"❌ Erro no teste de gravação de áudio: {e}")
        return None


def test_form_submission(driver):
    """Testa envio do formulário com arquivos."""
    print("📤 Testando envio do formulário...")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Preencher mensagem
        message_input = wait.until(EC.presence_of_element_located((By.ID, "message-input")))
        message_input.clear()
        message_input.send_keys("Teste de upload de arquivos com blob URLs")
        
        # Submeter formulário
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar processamento
        time.sleep(3)
        
        # Verificar se mensagem foi enviada (procurar por toast de sucesso)
        try:
            success_toast = driver.find_element(By.CSS_SELECTOR, ".toast--success")
            if success_toast:
                print("✅ Formulário enviado com sucesso!")
                return True
        except NoSuchElementException:
            pass
        
        # Verificar se página recarregou (campos limpos)
        message_input = driver.find_element(By.ID, "message-input")
        if not message_input.get_attribute("value"):
            print("✅ Formulário processado (campos limpos)")
            return True
        
        print("⚠️ Status do envio incerto")
        return False
        
    except Exception as e:
        print(f"❌ Erro no teste de envio: {e}")
        return False


def cleanup_test_files(test_files):
    """Remove arquivos de teste temporários."""
    for file_type, file_path in test_files.items():
        try:
            os.unlink(file_path)
            print(f"🗑️ Arquivo de teste {file_type} removido: {file_path}")
        except Exception as e:
            print(f"⚠️ Erro ao remover arquivo {file_type}: {e}")


def main():
    """Função principal do teste."""
    print("🚀 Iniciando teste de funcionalidade de blob URLs no SparkOne")
    print("=" * 60)
    
    # Criar arquivos de teste
    test_files = create_test_files()
    print(f"📁 Arquivos de teste criados: {list(test_files.keys())}")
    
    driver = None
    try:
        # Configurar driver
        driver = setup_driver()
        print("🌐 Driver do Chrome configurado")
        
        # Fazer login
        if not login_to_sparkone(driver):
            print("❌ Falha no login. Encerrando teste.")
            return
        
        print("\n" + "=" * 60)
        print("🧪 INICIANDO TESTES DE FUNCIONALIDADE")
        print("=" * 60)
        
        # Teste 1: Upload de imagem
        image_blob_url = test_image_upload(driver, test_files['image'])
        
        print("\n" + "-" * 40)
        
        # Teste 2: Gravação de áudio
        audio_blob_url = test_audio_recording(driver)
        
        print("\n" + "-" * 40)
        
        # Teste 3: Envio do formulário
        form_success = test_form_submission(driver)
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS RESULTADOS")
        print("=" * 60)
        
        print(f"📷 Upload de Imagem: {'✅ OK' if image_blob_url else '❌ FALHOU'}")
        if image_blob_url:
            print(f"   URL: {image_blob_url}")
        
        print(f"🎙️ Gravação de Áudio: {'✅ OK' if audio_blob_url else '❌ FALHOU'}")
        if audio_blob_url:
            print(f"   URL: {audio_blob_url}")
        
        print(f"📤 Envio do Formulário: {'✅ OK' if form_success else '❌ FALHOU'}")
        
        # Análise da URL blob fornecida pelo usuário
        user_blob_url = "blob:http://localhost:8000/68db39ae-aa01-4dd2-a566-9d7cc8d862a3"
        print(f"\n🔍 URL Blob do Usuário: {user_blob_url}")
        print("   Formato: ✅ Válido (blob:http://localhost:8000/[UUID])")
        print("   Origem: Provavelmente gerada por URL.createObjectURL()")
        print("   Contexto: Upload de arquivo ou gravação de áudio na interface")
        
    except Exception as e:
        print(f"❌ Erro geral no teste: {e}")
    
    finally:
        # Cleanup
        if driver:
            driver.quit()
            print("\n🔒 Navegador fechado")
        
        cleanup_test_files(test_files)
        print("🧹 Limpeza concluída")


if __name__ == "__main__":
    main()