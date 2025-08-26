# DevStack Health Monitor - Troubleshooting Guide

## 🔍 **Diagnosi Problemi**

### **1. Verifica Log DevStack**
```bash
# Log principale DevStack
tail -f /opt/stack/logs/stack.sh.log | grep health-monitor

# Log specifico del plugin
ls -la /opt/stack/logs/ | grep health

# Cerca errori nel log completo
grep -i "health-monitor" /opt/stack/logs/stack.sh.log
grep -i "error" /opt/stack/logs/stack.sh.log | grep health
```

### **2. Verifica Stato Repository**
```bash
# Controlla se il repository è stato clonato
ls -la /opt/stack/devstack-health-monitor/

# Se vuoto, clona manualmente
cd /opt/stack
git clone https://github.com/colby09/devstack-monitor-analysis.git devstack-monitor-analysis
```

### **3. Verifica Plugin DevStack**
```bash
# Controlla se il plugin è riconosciuto
cd /opt/stack/devstack
grep -r "health-monitor" .

# Verifica file plugin
ls -la /opt/stack/devstack-health-monitor/devstack/
```

### **4. Installazione Manuale**
Se il plugin non funziona, installa manualmente:

```bash
# 1. Clone repository
cd /opt/stack
git clone https://github.com/colby09/healthcheck-monitor.git devstack-health-monitor

# 2. Installa dipendenze Python
cd devstack-health-monitor/backend
pip3 install -r requirements.txt

# 3. Installa dipendenze Node.js
cd ..
npm install
npm run build

# 4. Configura environment
cd backend
cp .env.example .env

# Modifica .env con credenziali DevStack
nano .env
```

### **5. Configurazione .env**
```bash
# File: backend/.env
HOST=0.0.0.0
PORT=8080
DEBUG=true

# Credenziali DevStack (usa quelle del tuo ambiente)
OS_AUTH_URL=http://127.0.0.1/identity/v3
OS_PROJECT_NAME=admin
OS_USERNAME=admin
OS_PASSWORD=nomoresecret
OS_USER_DOMAIN_NAME=Default
OS_PROJECT_DOMAIN_NAME=Default

MONITOR_INTERVAL=30
MONITOR_TIMEOUT=10
MONITOR_RETRIES=3

CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0

DATABASE_URL=sqlite:///./health_monitor.db
SECRET_KEY=your-secret-key-change-in-production
```

### **6. Avvio Manuale**
```bash
# Terminal 1 - Backend
cd /opt/stack/devstack-health-monitor/backend
python3 main.py

# Terminal 2 - Verifica
curl http://localhost:8080/health
curl http://localhost:8080/api/instances
```

### **7. Test Connessione OpenStack**
```bash
# Source delle credenziali DevStack
source /opt/stack/devstack/openrc admin admin

# Test connessione
openstack server list
openstack service list
```

## 🚀 **Avvio Rapido**

Se vuoi testare subito senza plugin DevStack:

```bash
# 1. Clone
cd /opt/stack
git clone https://github.com/colby09/healthcheck-monitor.git devstack-health-monitor

# 2. Setup rapido
cd devstack-health-monitor
./quick-setup.sh  # Se esiste, altrimenti segui i passi manuali

# 3. Avvio
cd backend
python3 main.py &
cd ..
npm run dev
```

## 📋 **Checklist Risoluzione**

- [ ] Repository clonato in `/opt/stack/devstack-health-monitor/`
- [ ] Dipendenze Python installate
- [ ] Dipendenze Node.js installate  
- [ ] File `.env` configurato
- [ ] Credenziali OpenStack corrette
- [ ] Porta 8080 libera
- [ ] Servizi DevStack attivi

## 🔧 **Script di Setup Automatico**

Crea questo script per setup rapido:

```bash
#!/bin/bash
# File: quick-setup.sh

echo "🚀 DevStack Health Monitor - Setup Rapido"

# 1. Verifica DevStack
if [ ! -f "/opt/stack/devstack/openrc" ]; then
    echo "❌ DevStack non trovato!"
    exit 1
fi

# 2. Source credenziali
source /opt/stack/devstack/openrc admin admin

# 3. Setup backend
cd backend
pip3 install -r requirements.txt

# 4. Crea .env
cat > .env << EOF
HOST=0.0.0.0
PORT=8080
DEBUG=true

OS_AUTH_URL=$OS_AUTH_URL
OS_PROJECT_NAME=$OS_PROJECT_NAME
OS_USERNAME=$OS_USERNAME
OS_PASSWORD=$OS_PASSWORD
OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME
OS_PROJECT_DOMAIN_NAME=$OS_PROJECT_DOMAIN_NAME

MONITOR_INTERVAL=30
MONITOR_TIMEOUT=10
MONITOR_RETRIES=3

CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0

DATABASE_URL=sqlite:///./health_monitor.db
SECRET_KEY=$(openssl rand -hex 32)
EOF

# 5. Setup frontend
cd ..
npm install
npm run build

echo "✅ Setup completato!"
echo "🌐 Avvia con: cd backend && python3 main.py"
```