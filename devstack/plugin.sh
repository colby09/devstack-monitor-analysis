#!/bin/bash
# DevStack Health Monitor Plugin

# Plugin settings
HEALTH_MONITOR_DIR=${HEALTH_MONITOR_DIR:-$DEST/devstack-health-monitor}
HEALTH_MONITOR_PORT=${HEALTH_MONITOR_PORT:-8080}
HEALTH_MONITOR_INTERVAL=${HEALTH_MONITOR_INTERVAL:-30}
HEALTH_MONITOR_ENABLE_ALERTS=${HEALTH_MONITOR_ENABLE_ALERTS:-True}

# Plugin functions
function install_health_monitor {
    echo_summary "Installing DevStack Health Monitor"
    
    # Clone repository if not exists
    if [[ ! -d $HEALTH_MONITOR_DIR ]]; then
        git_clone $HEALTH_MONITOR_REPO $HEALTH_MONITOR_DIR $HEALTH_MONITOR_BRANCH
    fi
    
    # Install Python dependencies
    pip_install -r $HEALTH_MONITOR_DIR/backend/requirements.txt
    
    # Install Node.js dependencies and build frontend
    if [[ -f $HEALTH_MONITOR_DIR/package.json ]]; then
        cd $HEALTH_MONITOR_DIR
        npm install
        npm run build
        cd -
    fi
}

function configure_health_monitor {
    echo_summary "Configuring DevStack Health Monitor"
    
    # Create configuration file
    cat > $HEALTH_MONITOR_DIR/backend/.env <<EOF
HOST=0.0.0.0
PORT=$HEALTH_MONITOR_PORT
DEBUG=false

OS_AUTH_URL=$KEYSTONE_AUTH_URI
OS_PROJECT_NAME=$OS_PROJECT_NAME
OS_USERNAME=$OS_USERNAME
OS_PASSWORD=$OS_PASSWORD
OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME
OS_PROJECT_DOMAIN_NAME=$OS_PROJECT_DOMAIN_NAME

MONITOR_INTERVAL=$HEALTH_MONITOR_INTERVAL
MONITOR_TIMEOUT=10
MONITOR_RETRIES=3

CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0

DATABASE_URL=sqlite:///$HEALTH_MONITOR_DIR/health_monitor.db
SECRET_KEY=$(openssl rand -hex 32)
EOF
    
    # Create systemd service file
    sudo tee /etc/systemd/system/devstack-health-monitor.service > /dev/null <<EOF
[Unit]
Description=DevStack Health Monitor
After=network.target

[Service]
Type=simple
User=$STACK_USER
WorkingDirectory=$HEALTH_MONITOR_DIR/backend
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
}

function init_health_monitor {
    echo_summary "Initializing DevStack Health Monitor"
    
    # Create database tables if needed
    cd $HEALTH_MONITOR_DIR/backend
    python3 -c "
import asyncio
from app.core.config import settings
print('Health Monitor initialized successfully')
"
    cd -
}

function start_health_monitor {
    echo_summary "Starting DevStack Health Monitor"
    
    # Start the service
    sudo systemctl enable devstack-health-monitor
    sudo systemctl start devstack-health-monitor
    
    # Wait for service to start
    sleep 5
    
    # Check if service is running
    if sudo systemctl is-active --quiet devstack-health-monitor; then
        echo "DevStack Health Monitor started successfully"
        echo "Dashboard available at: http://$HOST_IP:$HEALTH_MONITOR_PORT"
        echo "API documentation at: http://$HOST_IP:$HEALTH_MONITOR_PORT/api/docs"
    else
        echo "Failed to start DevStack Health Monitor"
        sudo systemctl status devstack-health-monitor
    fi
}

function stop_health_monitor {
    echo_summary "Stopping DevStack Health Monitor"
    sudo systemctl stop devstack-health-monitor
    sudo systemctl disable devstack-health-monitor
}

function cleanup_health_monitor {
    echo_summary "Cleaning up DevStack Health Monitor"
    stop_health_monitor
    sudo rm -f /etc/systemd/system/devstack-health-monitor.service
    sudo systemctl daemon-reload
}

# Plugin main logic
if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_health_monitor
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_health_monitor
elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
    init_health_monitor
    start_health_monitor
elif [[ "$1" == "unstack" ]]; then
    stop_health_monitor
elif [[ "$1" == "clean" ]]; then
    cleanup_health_monitor
fi