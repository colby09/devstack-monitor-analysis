# DevStack Health Monitor - OpenStack Deployment

## 🚀 Quick Setup

1. **Unzip the project:**
   ```bash
   unzip devstack-health-monitor.zip
   cd project
   ```

2. **Run setup script:**
   ```bash
   chmod +x setup-openstack.sh
   ./setup-openstack.sh
   ```

3. **Start the backend:**
   ```bash
   source .venv/bin/activate
   cd backend
   python main.py
   ```

4. **Access the application:**
   - Frontend: `http://[your-ip]:8080`
   - API: `http://[your-ip]:8080/api`

## 🔧 Configuration

### Environment Variables (backend/.env)
```bash
# OpenStack Settings
DUMP_MODE=local
DUMP_LOCAL_DIRECTORY=/tmp/ramdump
FORENSIC_OUTPUT_DIR=/tmp/forensic_analysis

# API Settings
API_HOST=0.0.0.0
API_PORT=8080

# Security
SECRET_KEY=your-secret-key-here
```

## 🎯 Features

- ✅ **Memory Dumps**: virsh, dd, gcore methods
- ✅ **Forensic Analysis**: Binwalk, Foremost, YARA
- ✅ **PDF Reports**: Professional forensic reports
- ✅ **Real-time Progress**: WebSocket updates
- ✅ **Local Execution**: Optimized for OpenStack environment

## 🛠️ Manual Dependencies (if needed)

```bash
# If setup script fails, install manually:
sudo apt install -y binwalk foremost yara hexdump libvirt-clients qemu-utils
pip install fastapi uvicorn websockets python-multipart aiofiles reportlab
```

## 📋 Troubleshooting

### Permissions Issues:
```bash
sudo chown -R stack:stack /tmp/ramdump
sudo chmod 755 /tmp/ramdump
```

### LibVirt Access:
```bash
sudo usermod -a -G libvirt $USER
sudo systemctl restart libvirtd
```

### Firewall (if needed):
```bash
sudo ufw allow 8080
```

## 🔍 Testing

1. **Check backend health:**
   ```bash
   curl http://localhost:8080/health
   ```

2. **Test memory dump (mock):**
   - Go to Frontend → Forensics
   - Select any instance
   - Click "Start Memory Dump"

3. **View logs:**
   ```bash
   tail -f logs/backend.log
   ```
