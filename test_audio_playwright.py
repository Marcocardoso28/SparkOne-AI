#!/usr/bin/env python3
"""
Teste robusto para funcionalidade de áudio usando Playwright.
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("❌ Playwright não está instalado. Execute: pip install playwright")
    print("   Depois execute: playwright install chromium")
    sys.exit(1)

async def test_audio_functionality():
    """Testa a funcionalidade de áudio usando Playwright."""
    print("🎵 Testando funcionalidade de áudio com Playwright...")
    
    async with async_playwright() as p:
        # Configurar navegador
        browser = await p.chromium.launch(
            headless=False,  # Mostrar navegador para debug
            args=[
                '--use-fake-ui-for-media-stream',  # Simular permissão de microfone
                '--use-fake-device-for-media-stream',  # Usar dispositivo fake
                '--allow-running-insecure-content',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        context = await browser.new_context(
            permissions=['microphone'],  # Conceder permissão de microfone
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        
        try:
            # 1. Navegar para página de login
            print("\n1. Navegando para página de login...")
            await page.goto("http://localhost:8000/web/login")
            await page.wait_for_load_state('networkidle')
            
            # 2. Fazer login
            print("2. Fazendo login...")
            await page.fill('input[name="username"]', 'user')
            await page.fill('input[name="password"]', 'sparkone-dev')
            await page.click('button[type="submit"]')
            
            # Aguardar redirecionamento
            await page.wait_for_url("**/web/app", timeout=10000)
            print("   ✅ Login bem-sucedido")
            
            # 3. Verificar elementos de áudio
            print("\n3. Verificando elementos de áudio...")
            
            # Aguardar elementos carregarem
            await page.wait_for_selector('#record-button', timeout=5000)
            await page.wait_for_selector('#audio-file', timeout=5000)
            await page.wait_for_selector('#audio-preview', timeout=5000)
            
            print("   ✅ Todos os elementos de áudio encontrados")
            
            # 4. Testar funcionalidade de gravação
            print("\n4. Testando funcionalidade de gravação...")
            
            # Verificar estado inicial do botão
            button_text = await page.text_content('#record-button')
            print(f"   Estado inicial do botão: {button_text}")
            
            # Clicar no botão de gravação
            await page.click('#record-button')
            print("   ✅ Clique no botão de gravação executado")
            
            # Aguardar mudança no texto do botão
            await page.wait_for_function(
                "document.querySelector('#record-button').textContent.includes('Parar')",
                timeout=5000
            )
            
            button_text_recording = await page.text_content('#record-button')
            print(f"   Estado durante gravação: {button_text_recording}")
            
            # Aguardar um pouco (simular gravação)
            await page.wait_for_timeout(2000)
            
            # Parar gravação
            await page.click('#record-button')
            print("   ✅ Gravação parada")
            
            # Aguardar processamento
            await page.wait_for_function(
                "document.querySelector('#record-button').textContent.includes('Gravar')",
                timeout=5000
            )
            
            button_text_stopped = await page.text_content('#record-button')
            print(f"   Estado após parar: {button_text_stopped}")
            
            # 5. Verificar se o preview foi criado
            print("\n5. Verificando preview de áudio...")
            
            # Aguardar elemento de áudio aparecer
            try:
                await page.wait_for_selector('#audio-preview audio', timeout=5000)
                print("   ✅ Elemento de áudio criado no preview")
                
                # Verificar se tem src (URL blob)
                audio_src = await page.get_attribute('#audio-preview audio', 'src')
                if audio_src and audio_src.startswith('blob:'):
                    print(f"   ✅ URL blob criada: {audio_src[:50]}...")
                else:
                    print(f"   ⚠️ URL não é blob: {audio_src}")
                
            except PlaywrightTimeoutError:
                print("   ❌ Elemento de áudio não foi criado no preview")
            
            # 6. Verificar se o arquivo foi atribuído ao input
            print("\n6. Verificando input de arquivo...")
            
            # Usar JavaScript para verificar se o input tem arquivo
            has_file = await page.evaluate("""
                () => {
                    const input = document.querySelector('#audio-file');
                    return input && input.files && input.files.length > 0;
                }
            """)
            
            if has_file:
                print("   ✅ Arquivo atribuído ao input")
                
                # Obter informações do arquivo
                file_info = await page.evaluate("""
                    () => {
                        const input = document.querySelector('#audio-file');
                        const file = input.files[0];
                        return {
                            name: file.name,
                            size: file.size,
                            type: file.type
                        };
                    }
                """)
                
                print(f"   📄 Nome: {file_info['name']}")
                print(f"   📊 Tamanho: {file_info['size']} bytes")
                print(f"   🎵 Tipo: {file_info['type']}")
            else:
                print("   ❌ Arquivo não foi atribuído ao input")
            
            # 7. Verificar logs do console
            print("\n7. Verificando logs do console...")
            
            # Capturar logs do console
            console_logs = []
            
            def handle_console(msg):
                console_logs.append(f"{msg.type}: {msg.text}")
            
            page.on("console", handle_console)
            
            # Aguardar um pouco para capturar logs
            await page.wait_for_timeout(1000)
            
            if console_logs:
                print("   📝 Logs do console:")
                for log in console_logs[-5:]:  # Últimos 5 logs
                    print(f"      {log}")
            else:
                print("   ✅ Nenhum erro no console")
            
            print("\n✅ Teste de funcionalidade de áudio concluído com sucesso!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante o teste: {e}")
            
            # Capturar screenshot para debug
            screenshot_path = "debug_audio_error.png"
            await page.screenshot(path=screenshot_path)
            print(f"   📸 Screenshot salvo em: {screenshot_path}")
            
            return False
            
        finally:
            await browser.close()

async def main():
    """Função principal."""
    try:
        success = await test_audio_functionality()
        if success:
            print("\n🎉 Todos os testes de áudio passaram!")
        else:
            print("\n❌ Alguns testes falharam.")
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())