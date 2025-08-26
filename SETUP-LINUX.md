# DevStack Monitor and Analysis - Linux Setup

This document describes how to configure and start the DevStack Monitor and Analysis on a Linux machine with DevStack.

## Prerequisites

- Ubuntu/Debian system with DevStack installed
- Root or sudo access
- Internet connection to download dependencies

## Quick Installation

1. **Transfer the project**:
   ```bash
   # On Windows, create the archive
   ./package-for-transfer.sh
   
   # Transfer to Linux
   scp devstack-monitor-analysis-*.tar.gz user@192.168.78.190:~/
   ```

2. **Extract and setup**:
   ```bash
   # On Linux
   tar -xzf devstack-monitor-analysis-*.tar.gz
   cd devstack-monitor-analysis-*/
   chmod +x setup-linux.sh
   ./setup-linux.sh
   ```

3. **Start the monitor**:
   ```bash
   ./start-monitor.sh
   ```

## Manual Configuration

### 1. System Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm \
    build-essential libffi-dev libssl-dev gdb linux-tools-common
```

### 2. Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Frontend
```bash
npm install
npm run build
```

### 4. Dumps Directory
```bash
sudo mkdir -p /tmp/ramdump /tmp/dumps
sudo chown $USER:$USER /tmp/ramdump /tmp/dumps
```

### 5. OpenStack Variables
```bash
# Load DevStack variables
source /opt/stack/devstack/openrc admin admin

# Or set manually
export OS_AUTH_URL=http://localhost/identity/v3
export OS_PROJECT_NAME=admin
export OS_USERNAME=admin
export OS_PASSWORD=secret
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
```

## Memory Dumps

### SSH Key Setup
```bash
# Generate SSH key
ssh-keygen -t rsa -b 2048 -f /tmp/ssh_keys/openstack_key -N ""

# Show public key
cat /tmp/ssh_keys/openstack_key.pub
```

### Instance Configuration
To enable memory dumps, add the public key to instances:

1. **Cloud-init** (recommended):
   ```yaml
   #cloud-config
   ssh_authorized_keys:
     - ssh-rsa AAAAB3NzaC1yc2EAAAA... # your public key
   ```

2. **Manually** on instance:
   ```bash
   # On target instance
   echo "ssh-rsa AAAAB3NzaC1yc2EAAAA..." >> ~/.ssh/authorized_keys
   ```

## Usage

### Startup
```bash
./start-monitor.sh
```

### Access
- **Dashboard**: http://localhost:8080
- **API Docs**: http://localhost:8080/api/docs

### Test Setup
```bash
./test-setup.sh
```

## Memory Dump Tools

The system supports various memory dump methods on Linux:

1. **LiME** (Linux Memory Extractor)
2. **dd + /proc/kcore**
3. **gcore** (core dump)
4. **Mock mode** (for testing)

### Mode Configuration
In file `backend/app/core/config.py`:
```python
DUMP_MODE: str = "local"  # "local", "remote", or "mock"
```

## Troubleshooting

### Common Issues

1. **Dump permission errors**:
   ```bash
   sudo chown $USER:$USER /tmp/ramdump /tmp/dumps
   ```

2. **OpenStack connection failed**:
   ```bash
   source /opt/stack/devstack/openrc admin admin
   openstack server list  # test
   ```

3. **SSH dumps fail**:
   ```bash
   # Verify SSH key
   ssh -i /tmp/ssh_keys/openstack_key root@<instance-ip>
   
   # Verify connectivity
   ping <instance-ip>
   ```

4. **Port 8080 occupied**:
   ```bash
   # Change port in config.py
   PORT: int = 8081
   ```

### Logs
```bash
# Application logs
tail -f logs/app.log

# System logs
journalctl -f -u devstack-monitor-analysis
```

### Dump Directories
- **Local dumps**: `/tmp/ramdump/`
- **Remote dumps**: `/tmp/dumps/` (on instances)
- **SSH keys**: `/tmp/ssh_keys/`

## Performance

For optimal dumps:
- Use `local` mode when possible
- Configure sufficient memory on DevStack host
- Monitor disk space in `/tmp/`

## Security

- SSH keys are generated automatically
- Dumps contain sensitive data - handle with care
- API access is not authenticated (lab environment)

## Support

For issues:
1. Run `./test-setup.sh`
2. Check logs in `logs/`
3. Verify OpenStack connectivity
4. Test SSH to instances manually
