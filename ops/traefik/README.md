# Traefik Configuration

Este diretório contém a configuração de produção sugerida para o reverse proxy do SparkOne.

## Estrutura

- `traefik.yml`: configuração estática (entrypoints, resolutores ACME, métricas e dashboard).
- `dynamic/`: recursos dinâmicos versionados (rotas, middlewares, serviços).
- `acme.json`: arquivo **não versionado** onde o Traefik persiste certificados Let’s Encrypt.

## Passos para uso

1. No servidor, copie este diretório para `/etc/traefik` e garanta permissões `600` para `acme.json`:
   ```bash
   sudo mkdir -p /etc/traefik/dynamic
   sudo cp ops/traefik/traefik.yml /etc/traefik/
   sudo cp ops/traefik/dynamic/sparkone.yml /etc/traefik/dynamic/
   sudo touch /etc/traefik/acme.json
   sudo chmod 600 /etc/traefik/acme.json
   ```
2. Ajuste os domínios em `dynamic/sparkone.yml` conforme DNS disponível.
3. Configure as labels ou rede Docker para que o serviço `api` seja acessível via `http://api:8000`.
4. Execute o Traefik (ex.: `docker compose -f ops/staging-compose.yml up -d reverse-proxy`).

## Observabilidade

- O bloco `metrics.prometheus` habilita `/metrics` em Traefik (exponha via rede interna).
- Para visualizar o dashboard: atrele um router autenticado ou faça `kubectl port-forward` em ambientes clusters.

## Segurança

- Middlewares aplicam cabeçalhos HSTS, XSS e `referrer-policy`.
- Rate limiting básico (200 req/s com burst 100) pode ser ajustado conforme capacidade.
- `serversTransport.insecureSkipVerify` está definido como `false` para impedir backends sem TLS.

> Ajustes específicos da VPS (rede privada, autenticação mTLS, etc.) devem ser mantidos fora do repositório, mas documentados em `docs/infra.md`.
