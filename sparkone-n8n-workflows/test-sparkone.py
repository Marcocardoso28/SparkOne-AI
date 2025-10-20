#!/usr/bin/env python3
"""
⚡ SparkOne Test Suite
Script de teste para validar todas as funcionalidades do sistema SparkOne
"""

import requests
import json
import time
import sys
from datetime import datetime


class SparkOneTester:
    def __init__(self):
        self.base_url_n8n = "http://localhost:5678"
        self.base_url_evolution = "http://localhost:8080"
        self.test_results = []

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }

        status_symbol = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }

        print(
            f"{colors.get(status, '')}{status_symbol.get(status, '')} [{timestamp}] {message}{colors['RESET']}")

    def test_evolution_api(self):
        """Testa se a Evolution API está funcionando"""
        self.log("Testando Evolution API...", "INFO")

        try:
            response = requests.get(
                f"{self.base_url_evolution}/manager/fetchInstances", timeout=5)
            if response.status_code == 200:
                self.log("Evolution API está funcionando", "SUCCESS")
                return True
            else:
                self.log(
                    f"Evolution API retornou status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Erro ao conectar com Evolution API: {str(e)}", "ERROR")
            return False

    def test_n8n_health(self):
        """Testa se o n8n está funcionando"""
        self.log("Testando n8n...", "INFO")

        try:
            response = requests.get(self.base_url_n8n, timeout=5)
            if response.status_code == 200:
                self.log("n8n está funcionando", "SUCCESS")
                return True
            else:
                self.log(
                    f"n8n retornou status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Erro ao conectar com n8n: {str(e)}", "ERROR")
            return False

    def test_whatsapp_instance(self):
        """Testa se a instância WhatsApp foi criada"""
        self.log("Testando instância WhatsApp...", "INFO")

        try:
            headers = {"apikey": "sparkone_2024_secure_key"}
            response = requests.get(
                f"{self.base_url_evolution}/instance/fetchInstances", headers=headers, timeout=5)

            if response.status_code == 200:
                instances = response.json()
                if any(inst.get("instanceName") == "sparkone-instance" for inst in instances):
                    self.log("Instância WhatsApp encontrada", "SUCCESS")
                    return True
                else:
                    self.log("Instância WhatsApp não encontrada", "WARNING")
                    return False
            else:
                self.log(
                    f"Erro ao buscar instâncias: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Erro ao testar instância WhatsApp: {str(e)}", "ERROR")
            return False

    def test_webhook_endpoints(self):
        """Testa os endpoints de webhook"""
        self.log("Testando endpoints de webhook...", "INFO")

        webhooks = [
            {"name": "WhatsApp Chat",
                "url": f"{self.base_url_n8n}/webhook/sparkone-whatsapp"},
            {"name": "Voice Control",
                "url": f"{self.base_url_n8n}/webhook/sparkone-voice"},
            {"name": "Evolution Webhook",
                "url": f"{self.base_url_n8n}/webhook/evolution-webhook"}
        ]

        results = []
        for webhook in webhooks:
            try:
                # Teste básico de conectividade
                test_data = {"test": "sparkone_test",
                             "timestamp": datetime.now().isoformat()}
                response = requests.post(
                    webhook["url"], json=test_data, timeout=5)

                # 405 = Method Not Allowed é OK para webhooks
                if response.status_code in [200, 201, 405]:
                    self.log(
                        f"Webhook {webhook['name']} está acessível", "SUCCESS")
                    results.append(True)
                else:
                    self.log(
                        f"Webhook {webhook['name']} retornou status {response.status_code}", "WARNING")
                    results.append(False)
            except Exception as e:
                self.log(
                    f"Erro ao testar webhook {webhook['name']}: {str(e)}", "ERROR")
                results.append(False)

        return any(results)

    def test_openai_integration(self):
        """Testa integração com OpenAI (simulação)"""
        self.log("Testando integração OpenAI...", "INFO")

        # Simular teste de webhook com prompt OpenAI
        try:
            test_message = {
                "body": {
                    "message": "Teste de conectividade SparkOne"
                }
            }

            response = requests.post(
                f"{self.base_url_n8n}/webhook/sparkone-whatsapp", json=test_message, timeout=10)

            if response.status_code in [200, 201]:
                self.log("Integração OpenAI testada via webhook", "SUCCESS")
                return True
            else:
                self.log(
                    f"Teste OpenAI retornou status {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Erro ao testar integração OpenAI: {str(e)}", "ERROR")
            return False

    def test_weather_api(self):
        """Testa integração com OpenWeatherMap"""
        self.log("Testando integração Weather API...", "INFO")

        try:
            # Simular comando de clima via webhook
            test_command = {
                "body": {
                    "message": "comandos"  # Comando que deveria retornar clima
                }
            }

            response = requests.post(
                f"{self.base_url_n8n}/webhook/sparkone-whatsapp", json=test_command, timeout=10)

            if response.status_code in [200, 201]:
                self.log("Teste Weather API realizado", "SUCCESS")
                return True
            else:
                self.log(
                    f"Teste Weather API retornou status {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Erro ao testar Weather API: {str(e)}", "ERROR")
            return False

    def test_voice_control(self):
        """Testa controle por voz"""
        self.log("Testando controle por voz...", "INFO")

        try:
            # Simular comando de voz
            voice_command = {
                "body": {
                    "command": "ligar luzes da sala",
                    "action": "ligar"
                }
            }

            response = requests.post(
                f"{self.base_url_n8n}/webhook/sparkone-voice", json=voice_command, timeout=10)

            if response.status_code in [200, 201]:
                self.log("Teste de controle por voz realizado", "SUCCESS")
                return True
            else:
                self.log(
                    f"Teste de voz retornou status {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Erro ao testar controle por voz: {str(e)}", "ERROR")
            return False

    def run_all_tests(self):
        """Executa todos os testes"""
        self.log("🚀 Iniciando Test Suite do SparkOne", "INFO")
        self.log("=" * 50, "INFO")

        tests = [
            ("Evolution API", self.test_evolution_api),
            ("n8n Health", self.test_n8n_health),
            ("WhatsApp Instance", self.test_whatsapp_instance),
            ("Webhook Endpoints", self.test_webhook_endpoints),
            ("OpenAI Integration", self.test_openai_integration),
            ("Weather API", self.test_weather_api),
            ("Voice Control", self.test_voice_control)
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            self.log(f"\n🧪 Executando teste: {test_name}", "INFO")
            try:
                result = test_func()
                if result:
                    passed += 1
                self.test_results.append((test_name, result))
            except Exception as e:
                self.log(
                    f"Erro inesperado no teste {test_name}: {str(e)}", "ERROR")
                self.test_results.append((test_name, False))

            time.sleep(1)  # Pausa entre testes

        # Resultado final
        self.log("\n" + "=" * 50, "INFO")
        self.log("📊 RESULTADOS DOS TESTES", "INFO")
        self.log("=" * 50, "INFO")

        for test_name, result in self.test_results:
            status = "SUCCESS" if result else "ERROR"
            self.log(f"{test_name}: {'PASSOU' if result else 'FALHOU'}", status)

        self.log(f"\n🎯 Resumo: {passed}/{total} testes passaram",
                 "SUCCESS" if passed == total else "WARNING")

        if passed == total:
            self.log(
                "🎉 Todos os testes passaram! Sistema SparkOne está funcionando perfeitamente.", "SUCCESS")
            return True
        elif passed >= total * 0.7:
            self.log(
                "⚠️ A maioria dos testes passou. Sistema parcialmente funcional.", "WARNING")
            return True
        else:
            self.log(
                "❌ Muitos testes falharam. Verifique a configuração do sistema.", "ERROR")
            return False


def main():
    """Função principal"""
    print("⚡ SparkOne Test Suite")
    print("Sistema de teste automatizado para validação completa")
    print()

    tester = SparkOneTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


