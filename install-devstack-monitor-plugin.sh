#!/bin/bash

# DevStack Monitor and Analysis Plugin - Installation Script
# 
# This script automates the installation and integration of the DevStack Monitor 
# and Analysis plugin into a DevStack environment.
#
# The plugin provides:
# - Real-time monitoring of OpenStack services and instances
# - Memory dump analysis and forensic capabilities  
# - Integrated web dashboard for monitoring and analysis
# - Multi-tool forensic analysis pipeline
#
# Prerequisites:
# - DevStack environment already installed and configured
# - Git, Node.js, and Python available
# - Sudo privileges for system configuration
#
# Usage:
#   ./install-devstack-monitor-plugin.sh [--local-conf-path /opt/stack/devstack/local.conf]

set -e  # Exit on any error

# Configuration
PLUGIN_NAME="devstack-monitor-analysis"
PLUGIN_REPO_URL="https://github.com/colby09/devstack-monitor-analysis.git"
DEFAULT_LOCAL_CONF="/opt/stack/devstack/local.conf"
DEVSTACK_DIR="/opt/stack/devstack"
PLUGIN_DIR="/opt/stack/$PLUGIN_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
LOCAL_CONF_PATH="$DEFAULT_LOCAL_CONF"
while [[ $# -gt 0 ]]; do
    case $1 in
        --local-conf-path)
            LOCAL_CONF_PATH="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--local-conf-path /path/to/local.conf]"
            echo ""
            echo "Options:"
            echo "  --local-conf-path    Path to DevStack local.conf file (default: $DEFAULT_LOCAL_CONF)"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info "Starting DevStack Monitor and Analysis Plugin installation..."

# Check if DevStack is installed
if [[ ! -d "$DEVSTACK_DIR" ]]; then
    log_error "DevStack not found at $DEVSTACK_DIR"
    log_error "Please install DevStack first before running this script"
    exit 1
fi

# Check if local.conf exists
if [[ ! -f "$LOCAL_CONF_PATH" ]]; then
    log_error "local.conf not found at $LOCAL_CONF_PATH"
    log_error "Please specify the correct path with --local-conf-path"
    exit 1
fi

log_success "Found DevStack installation at $DEVSTACK_DIR"
log_success "Found local.conf at $LOCAL_CONF_PATH"

# Step 1: Clone or update plugin repository
log_info "Step 1: Setting up plugin repository..."

if [[ -d "$PLUGIN_DIR" ]]; then
    log_warning "Plugin directory already exists at $PLUGIN_DIR"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PLUGIN_DIR"
        git pull origin main
        log_success "Plugin repository updated"
    else
        log_info "Skipping repository update"
    fi
else
    log_info "Cloning plugin repository..."
    git clone "$PLUGIN_REPO_URL" "$PLUGIN_DIR"
    log_success "Plugin repository cloned to $PLUGIN_DIR"
fi

cd "$PLUGIN_DIR"

# Step 2: Install system dependencies
log_info "Step 2: Installing system dependencies..."

# Update package manager
sudo apt-get update

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    log_info "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    log_success "Node.js installed successfully"
else
    log_success "Node.js already installed ($(node --version))"
fi

# Install forensic analysis tools
log_info "Installing forensic analysis tools..."
sudo apt-get install -y \
    binutils \
    foremost \
    hexdump \
    yara \
    python3-yara \
    strings

log_success "Forensic analysis tools installed"

# Step 3: Set up Python environment
log_info "Step 3: Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    log_success "Python virtual environment created"
fi

# Activate virtual environment and install dependencies
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

log_success "Python dependencies installed"

# Step 4: Set up Node.js dependencies and build frontend
log_info "Step 4: Setting up frontend..."

npm install
npm run build

log_success "Frontend built successfully"

# Step 5: Configure DevStack plugin integration
log_info "Step 5: Configuring DevStack integration..."

# Create backup of local.conf
cp "$LOCAL_CONF_PATH" "$LOCAL_CONF_PATH.backup.$(date +%Y%m%d_%H%M%S)"
log_success "Backup of local.conf created"

# Add plugin configuration to local.conf if not already present
PLUGIN_CONFIG="
# DevStack Monitor and Analysis Plugin
enable_plugin $PLUGIN_NAME $PLUGIN_DIR
"

if ! grep -q "enable_plugin $PLUGIN_NAME" "$LOCAL_CONF_PATH"; then
    echo "$PLUGIN_CONFIG" >> "$LOCAL_CONF_PATH"
    log_success "Plugin configuration added to local.conf"
else
    log_warning "Plugin configuration already exists in local.conf"
fi

# Step 6: Create plugin activation script
log_info "Step 6: Creating plugin activation script..."

cat > "$PLUGIN_DIR/activate-plugin.sh" << 'EOF'
#!/bin/bash

# DevStack Monitor and Analysis Plugin Activation Script
# Run this script to start the monitoring and analysis services

set -e

PLUGIN_DIR="/opt/stack/devstack-monitor-analysis"
cd "$PLUGIN_DIR"

echo "Starting DevStack Monitor and Analysis Plugin..."

# Activate Python virtual environment
source .venv/bin/activate

# Start the backend service
echo "Starting backend service on port 8080..."
cd backend
python main.py &
BACKEND_PID=$!

echo "Backend service started with PID: $BACKEND_PID"
echo "Dashboard available at: http://localhost:8080"
echo ""
echo "Services running:"
echo "- Web Dashboard: http://localhost:8080"
echo "- API Endpoints: http://localhost:8080/api"
echo "- Metrics: http://localhost:8080/api/metrics/summary"
echo "- Instance Management: http://localhost:8080/api/instances"
echo "- Forensic Analysis: http://localhost:8080/api/forensic"
echo ""
echo "To stop the services, run: kill $BACKEND_PID"
echo "Or use Ctrl+C if running in foreground"

# Wait for backend to finish (if running in foreground)
wait $BACKEND_PID
EOF

chmod +x "$PLUGIN_DIR/activate-plugin.sh"
log_success "Plugin activation script created"

# Step 7: Create systemd service (optional)
log_info "Step 7: Creating systemd service..."

sudo tee /etc/systemd/system/devstack-monitor.service > /dev/null << EOF
[Unit]
Description=DevStack Monitor and Analysis Service
After=network.target

[Service]
Type=simple
User=stack
WorkingDirectory=$PLUGIN_DIR/backend
Environment=PATH=$PLUGIN_DIR/.venv/bin
ExecStart=$PLUGIN_DIR/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
log_success "Systemd service created (devstack-monitor.service)"

# Step 8: Set up log rotation
log_info "Step 8: Setting up log rotation..."

sudo tee /etc/logrotate.d/devstack-monitor > /dev/null << EOF
$PLUGIN_DIR/backend/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 stack stack
}
EOF

log_success "Log rotation configured"

# Step 9: Create forensic analysis directory structure
log_info "Step 9: Setting up forensic analysis environment..."

sudo mkdir -p /home/stack/forensic/{reports,dumps,temp}
sudo chown -R stack:stack /home/stack/forensic
sudo chmod -R 755 /home/stack/forensic

# Create memory dump directories
log_info "Creating memory dump directories..."
sudo mkdir -p /tmp/ramdump /tmp/dumps
sudo chown -R stack:stack /tmp/ramdump /tmp/dumps
sudo chmod -R 755 /tmp/ramdump /tmp/dumps

# Ensure forensic scripts are executable (they are now in the plugin directory)
chmod +x "$PLUGIN_DIR/multi-tool-forensic.sh"
chmod +x "$PLUGIN_DIR/advanced-yara-tool.sh"
log_success "Forensic scripts configured in plugin directory"

log_success "Forensic analysis environment configured"

# Final steps and verification
log_info "Step 10: Final verification and setup..."

# Test if the plugin can be imported
cd "$PLUGIN_DIR"
source .venv/bin/activate
python -c "
import sys
sys.path.append('backend')
from app.core.config import settings
print('✓ Plugin configuration loaded successfully')
" 2>/dev/null && log_success "Plugin configuration verified" || log_warning "Plugin configuration test failed"

# Create quick test script
cat > "$PLUGIN_DIR/test-installation.sh" << 'EOF'
#!/bin/bash

echo "Testing DevStack Monitor and Analysis Plugin installation..."

# Test Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js: $(node --version)"
else
    echo "✗ Node.js not found"
fi

# Test Python environment
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    if python -c "import fastapi, uvicorn" 2>/dev/null; then
        echo "✓ Python environment with FastAPI"
    else
        echo "✗ Python environment missing dependencies"
    fi
else
    echo "✗ Python virtual environment not found"
fi

# Test forensic tools
TOOLS=("binwalk" "foremost" "strings" "hexdump" "yara")
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "✓ Forensic tool: $tool"
    else
        echo "✗ Forensic tool missing: $tool"
    fi
done

# Test directories
if [[ -d "/home/stack/forensic" ]]; then
    echo "✓ Forensic analysis directory"
else
    echo "✗ Forensic analysis directory missing"
fi

if [[ -d "/tmp/ramdump" ]]; then
    echo "✓ Local memory dump directory (/tmp/ramdump)"
else
    echo "✗ Local memory dump directory missing"
fi

if [[ -d "/tmp/dumps" ]]; then
    echo "✓ Remote memory dump directory (/tmp/dumps)"
else
    echo "✗ Remote memory dump directory missing"
fi

# Test forensic scripts
if [[ -f "$PLUGIN_DIR/multi-tool-forensic.sh" ]]; then
    echo "✓ Multi-tool forensic script"
else
    echo "✗ Multi-tool forensic script missing"
fi

if [[ -f "$PLUGIN_DIR/advanced-yara-tool.sh" ]]; then
    echo "✓ Advanced YARA forensic script"
else
    echo "✗ Advanced YARA forensic script missing"
fi

echo ""
echo "Installation test completed."
EOF

chmod +x "$PLUGIN_DIR/test-installation.sh"

log_success "Installation test script created"

# Print final summary
echo ""
echo "================================================================"
log_success "DevStack Monitor and Analysis Plugin installation completed!"
echo "================================================================"
echo ""
echo "📋 Installation Summary:"
echo "   • Plugin installed at: $PLUGIN_DIR"
echo "   • Configuration added to: $LOCAL_CONF_PATH"
echo "   • Systemd service: devstack-monitor.service"
echo "   • Forensic analysis directory: /home/stack/forensic"
echo "   • Memory dump directories: /tmp/ramdump, /tmp/dumps"
echo "   • Forensic scripts: $PLUGIN_DIR/*.sh"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Restart DevStack to activate the plugin:"
echo "   cd $DEVSTACK_DIR && ./unstack.sh && ./stack.sh"
echo ""
echo "2. Or start the plugin manually:"
echo "   $PLUGIN_DIR/activate-plugin.sh"
echo ""
echo "3. Or use systemd service:"
echo "   sudo systemctl enable devstack-monitor"
echo "   sudo systemctl start devstack-monitor"
echo ""
echo "4. Test the installation:"
echo "   $PLUGIN_DIR/test-installation.sh"
echo ""
echo "🌐 Access Points:"
echo "   • Web Dashboard: http://localhost:8080"
echo "   • API Documentation: http://localhost:8080/docs"
echo "   • Metrics Endpoint: http://localhost:8080/api/metrics/summary"
echo ""
echo "📚 Documentation:"
echo "   • README.md: General plugin information"
echo "   • DEPLOYMENT.md: Deployment guide"
echo "   • FORENSICS-TEST-GUIDE.md: Forensic analysis testing"
echo ""
echo "🔧 Management Commands:"
echo "   • Start: sudo systemctl start devstack-monitor"
echo "   • Stop: sudo systemctl stop devstack-monitor"
echo "   • Status: sudo systemctl status devstack-monitor"
echo "   • Logs: journalctl -u devstack-monitor -f"
echo ""
log_success "Installation completed successfully! 🎉"
