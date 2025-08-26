# 🔬 Forensics System - Complete Test Guide

## DevStack Server Setup

1. **Transfer archive:**
   ```bash
   # On DevStack server
   wget https://github.com/colby09/devstack-monitor-analysis/archive/main.tar.gz
   # or with scp from Windows:
   # scp project-forensics-complete.tar.gz stack@192.168.1.100:~/
   ```

2. **Test system:**
   ```bash
   chmod +x test-forensics-system.sh
   ./test-forensics-system.sh
   ```

## System Startup

1. **Setup Virtual Environment (one time only):**
   ```bash
   cd devstack-monitor-analysis
   chmod +x setup-venv-local.sh
   ./setup-venv-local.sh
   ```

2. **Backend (Terminal 1):**
   ```bash
   cd devstack-monitor-analysis
   chmod +x start-monitor-local.sh
   ./start-monitor-local.sh
   ```

3. **Frontend (Terminal 2):**
   ```bash
   cd devstack-monitor-analysis
   npm install  # Only if needed
   npm run dev
   ```

## Complete Workflow Test

### 1. Test Instance Creation
```bash
# Check available instances
openstack server list

# If needed, create test instance
openstack server create \
  --flavor cirros256 \
  --image cirros-0.6.2-x86_64-disk \
  --network private \
  forensics-test-vm
```

### 2. Memory Dump Test
- Go to http://localhost:5173/instances
- Select the `forensics-test-vm` instance
- Click "Dump RAM" 
- Verify dump created (should be ~521MB)

### 3. Forensics Analysis Test
- Go to http://localhost:5173/forensics
- Select the instance with available dump
- Configure analysis (all types selected)
- Start analysis and monitor progress
- Verify results in tabs:
  - **Processes**: Kernel/user process list
  - **Network**: Network connections
  - **Files**: Open files
  - **Modules**: Kernel modules
  - **System**: General system info

### 4. Backend Verification
```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/v1/forensics/analyses
curl -X POST http://localhost:8000/api/v1/forensics/analyze \
  -H "Content-Type: application/json" \
  -d '{"dump_id": "xxx", "analysis_types": ["processes", "network"]}'
```

## Forensics File System

### Backend:
- `app/models/forensic.py` - Analysis data models
- `app/services/forensic_analysis.py` - Volatility service 
- `app/api/endpoints/forensics.py` - REST API

### Frontend:
- `src/pages/Forensics.tsx` - Main dashboard
- `src/components/ui/` - UI components (tabs, progress, etc)

## Troubleshooting

### Volatility Path:
```bash
# Verify Volatility path
ls -la /tmp/volatility3-2.26.0/vol.py
export VOLATILITY_PATH="/tmp/volatility3-2.26.0"
```

### Virsh Permissions:
```bash
# If permission errors
sudo usermod -a -G libvirt $USER
sudo systemctl restart libvirtd
```

### Memory Dump Issues:
```bash
# Verify libvirt domains
sudo virsh list --all
sudo virsh domblklist <instance-id>
```

## Success Tests

✅ **Memory Dump**: ~521MB .dump file created
✅ **Volatility**: Banner detection working  
✅ **API**: Forensics endpoints responding
✅ **Frontend**: Dashboard shows progress and results
✅ **Analysis**: All Volatility plugins working
✅ **UI**: Tab navigation and data visualization

## Future Developments

- Export results to CSV/JSON
- Comparative analysis between dumps
- Automatic alerts on anomalies  
- Timeline analysis integration
- Custom Volatility plugins
