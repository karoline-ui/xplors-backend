# 🎯 DEPLOY NO CLOUD RUN - PASSO A PASSO VISUAL

## 📋 PRÉ-REQUISITOS

```
✅ Conta Google
✅ Repositório no GitHub com este código
✅ Chaves: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

---

## 🚀 PASSO A PASSO (15 MINUTOS)

### PASSO 1: ACESSAR GOOGLE CLOUD CONSOLE

**URL:** https://console.cloud.google.com

1. Fazer login com sua conta Google
2. Aceitar termos (se primeira vez)

---

### PASSO 2: CRIAR/SELECIONAR PROJETO

**Tela:** Canto superior esquerdo, ao lado do logo Google Cloud

1. Clicar no **seletor de projetos** (dropdown)
2. Clicar em **"NEW PROJECT"** (botão no topo do modal)
3. Preencher:
   ```
   Project name: xplors-backend
   Organization: (deixar padrão)
   Location: (deixar padrão)
   ```
4. Clicar em **"CREATE"**
5. Aguardar criação (~30 segundos)
6. Selecionar o projeto criado

**OU**

Se já tem projeto, apenas selecionar

---

### PASSO 3: ATIVAR BILLING (OBRIGATÓRIO)

**Tela:** Aparecerá automaticamente se não tiver billing

1. Clicar em **"ENABLE BILLING"**
2. Selecionar conta de billing existente **OU**
3. Criar nova:
   - Nome: "Xplors"
   - País: Brasil
   - Adicionar cartão de crédito
   - Clicar **"START MY FREE TRIAL"** (ganha $300 grátis)

**IMPORTANTE:** Não será cobrado sem seu consentimento!

---

### PASSO 4: ACESSAR CLOUD RUN

**Menu lateral → Cloud Run**

**OU**

**Buscar:** Na barra de busca superior, digite "Cloud Run"

**OU**

**URL direta:** https://console.cloud.google.com/run

---

### PASSO 5: HABILITAR API (SE NECESSÁRIO)

**Tela:** Se aparecer "Enable Cloud Run API"

1. Clicar em **"ENABLE"**
2. Aguardar (~1 minuto)

---

### PASSO 6: CRIAR SERVIÇO

**Tela:** Cloud Run → Serviços (vazia)

1. Clicar no botão azul **"CREATE SERVICE"** (no topo)

---

### PASSO 7: CONFIGURAR SOURCE

**Tela:** Create service

**Seção:** "Source"

1. Selecionar: **"Continuously deploy from a repository (source or function)"**
2. Clicar em **"SET UP WITH CLOUD BUILD"**

---

### PASSO 8: CONECTAR GITHUB

**Tela:** Set up source repository

**Seção:** "Repository Provider"

1. Selecionar: **"GitHub"**
2. Clicar em **"MANAGE CONNECTED REPOSITORIES"**

**Nova aba abrirá:**

3. Clicar em **"Connect to GitHub"**
4. Autorizar Google Cloud Build
5. Selecionar:
   - **"All repositories"** (mais fácil)
   - OU **"Only select repositories"** → escolher seu repo
6. Clicar em **"Install"**
7. Fechar a aba
8. Voltar para aba do Cloud Run

---

### PASSO 9: SELECIONAR REPOSITÓRIO

**Tela:** Set up source repository (atualizada)

**Seção:** "Repository"

1. Clicar no dropdown **"Repository"**
2. Encontrar e selecionar: **seu-usuario/xplors-backend**
3. **Branch:** `main` (ou `master`)
4. **Build Type:** Deixar "Go, Node.js, Python, Java, .NET Core, Ruby, or PHP via Google Cloud's buildpacks"
5. Clicar em **"SAVE"**

---

### PASSO 10: CONFIGURAR SERVIÇO

**Tela:** Create service (voltou)

**Seção:** "Service name"
```
Service name: xplors-backend
Region: us-central1 (Iowa)
```

**IMPORTANTE:** Escolher região próxima aos usuários!
- 🇧🇷 Brasil: `southamerica-east1` (São Paulo)
- 🇺🇸 EUA: `us-central1` (Iowa)
- 🇪🇺 Europa: `europe-west1` (Bélgica)

---

### PASSO 11: CONFIGURAR CPU E MEMORY

**Seção:** "CPU allocation and pricing"

1. Deixar: **"CPU is only allocated during request processing"**

**Seção:** "Autoscaling"
```
Minimum number of instances: 0
Maximum number of instances: 10
```

**Seção:** "Instance"
```
CPU: 1
Memory: 1 GiB
Request timeout: 300 segundos
```

---

### PASSO 12: CONFIGURAR INGRESS

**Seção:** "Ingress"

1. Selecionar: **"Allow all traffic"**

**Seção:** "Authentication"

1. Selecionar: **"Allow unauthenticated invocations"**

**IMPORTANTE:** Necessário para API pública!

---

### PASSO 13: ADICIONAR VARIÁVEIS DE AMBIENTE

**Seção:** "Container, Variables & Secrets, Connections, Security"

1. Clicar para expandir
2. Ir na aba **"VARIABLES & SECRETS"**
3. Clicar em **"ADD VARIABLE"** (4 vezes)

**Adicionar:**

```
Nome: OPENAI_API_KEY
Valor: sk-proj-...sua-chave-aqui

Nome: SUPABASE_URL
Valor: https://xxxxx.supabase.co

Nome: SUPABASE_KEY
Valor: eyJhbGci...sua-chave-aqui

Nome: LIMITE_MENSAL
Valor: 100.0
```

**DICA:** Clicar em **"REFERENCE A SECRET"** se quiser mais segurança!

---

### PASSO 14: CRIAR!

**No final da página:**

1. Revisar configurações
2. Clicar no botão azul **"CREATE"** (no rodapé)

---

### PASSO 15: AGUARDAR DEPLOY

**Tela:** Service details

**O que acontece:**
```
1. ⏳ Building...           (2-5 min)
   - Clonando repositório
   - Detectando Dockerfile
   - Building imagem Docker
   - Pushing para Container Registry

2. ⏳ Deploying...          (1-2 min)
   - Criando revision
   - Alocando recursos
   - Iniciando containers

3. ✅ Ready!                (Done!)
   - Serviço ativo
   - URL disponível
```

**Ver progresso:**
- Seção **"REVISIONS"** → Última revisão
- Ou **"LOGS"** → Ver build em tempo real

---

### PASSO 16: PEGAR URL DO SERVIÇO

**Tela:** Service details

**Seção:** No topo, verá:

```
✅ xplors-backend

https://xplors-backend-xxx-uc.a.run.app

[EDIT] [DELETE] [...]
```

**Copiar essa URL!**

Exemplo:
```
https://xplors-backend-abc123xyz-uc.a.run.app
```

---

### PASSO 17: TESTAR!

**No navegador:**

```
https://sua-url.run.app/health
```

**Deve retornar:**
```json
{
  "status": "ok",
  "openai": "configured",
  "supabase": "connected",
  "versao": "GCP-MERCHANDISING",
  "features": [...]
}
```

**✅ FUNCIONOU!**

---

## 🔄 DEPLOY AUTOMÁTICO (BONUS)

**Agora:**

Cada **push no GitHub** = **Deploy automático!**

```bash
git add .
git commit -m "feat: nova feature"
git push origin main

# Cloud Build detecta
# Build automático
# Deploy automático
# Zero downtime!
```

**Ver progresso:**
Cloud Run → xplors-backend → REVISIONS

---

## 🔧 CONFIGURAÇÕES PÓS-DEPLOY

### Atualizar Frontend:

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://sua-url.run.app
```

### Custom Domain (Opcional):

1. Cloud Run → xplors-backend
2. **MANAGE CUSTOM DOMAINS**
3. Adicionar seu domínio
4. Seguir instruções DNS

---

## 📊 MONITORAMENTO

### Ver Logs:

**Cloud Run → xplors-backend → LOGS**

Ou:

**URL:** https://console.cloud.google.com/logs

### Ver Métricas:

**Cloud Run → xplors-backend → METRICS**

Gráficos de:
- Requests/segundo
- Latência
- Erros
- Instâncias ativas

### Ver Custos:

**Menu → Billing → Reports**

---

## 🔐 SEGURANÇA

### Usar Secrets Manager (Recomendado):

1. **Menu → Security → Secret Manager**
2. **CREATE SECRET**
3. Nome: `openai-api-key`
4. Valor: `sk-...`
5. **CREATE**

**No Cloud Run:**
1. Edit service
2. VARIABLES & SECRETS
3. **REFERENCE A SECRET**
4. Selecionar secret
5. Env variable: `OPENAI_API_KEY`
6. **DEPLOY**

---

## 💰 CONTROLAR CUSTOS

### Limitar instâncias:

**Edit service → Autoscaling**
```
Max instances: 5  (em vez de 10)
```

### Reduzir recursos:

**Edit service → Instance**
```
Memory: 512 MiB  (em vez de 1 GiB)
CPU: 0.5         (em vez de 1)
```

### Billing Alerts:

**Menu → Billing → Budgets & alerts**
1. **CREATE BUDGET**
2. Nome: "Xplors Alert"
3. Budget amount: $20/mês
4. Alert threshold: 80%
5. **FINISH**

---

## 🐛 TROUBLESHOOTING

### Erro: "Permission denied"

**Solução:** Habilitar billing no projeto

### Erro: "Build failed"

**Ver logs:**
Cloud Run → Service → LOGS → Filtrar "build"

**Comum:**
- requirements.txt errado
- Dockerfile com erro
- Porta errada (usar 8080)

### Erro: "Out of memory"

**Solução:** Aumentar memory para 2 GiB

### Erro: "Service Unavailable"

**Causa:** Cold start (primeira request)

**Solução:**
- Aguardar 10 segundos
- Ou configurar `min instances: 1`

---

## 📞 LINKS ÚTEIS

- **Console:** https://console.cloud.google.com
- **Cloud Run:** https://console.cloud.google.com/run
- **Logs:** https://console.cloud.google.com/logs
- **Billing:** https://console.cloud.google.com/billing
- **Docs:** https://cloud.google.com/run/docs

---

## ✅ CHECKLIST FINAL

```
□ Criei projeto no GCP
□ Ativei billing
□ Habilitei Cloud Run API
□ Conectei GitHub
□ Configurei variáveis de ambiente
□ Deploy concluído (status: Ready)
□ Testei /health (retornou ok)
□ Copiei URL do serviço
□ Atualizei NEXT_PUBLIC_API_URL no frontend
□ Testei upload de planilha (funciona!)
□ Testei análise de imagem (funciona!)
```

---

## 🎉 PRONTO!

**Backend no ar com:**
- ✅ HTTPS automático
- ✅ Escalável
- ✅ Deploy automático
- ✅ $300 grátis (free trial)
- ✅ Logs em tempo real
- ✅ Métricas detalhadas

**Custo estimado: $2-5/mês**

---

**🚀 BACKEND EM PRODUÇÃO! 💜**
