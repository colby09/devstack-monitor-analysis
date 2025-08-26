#!/bin/bash
# Script to configure the .env file

echo "⚙️ Environment file configuration for DevStack Monitor and Analysis"
echo "=================================================================="

# Go to backend directory
cd /opt/stack/devstack-monitor-analysis/backend

# Check if .env.example exists
if [ -f ".env.example" ]; then
    echo "✅ .env.example file found"
    
    # Copy .env.example to .env
    cp .env.example .env
    echo "✅ .env file created from .env.example"
else
    echo "❌ .env.example file not found, creating .env from scratch..."
    
    # Create .env from scratch
    cat > .env << 'EOF'
# Server Configuration
HOST=0.0.0.0
PORT=8080
DEBUG=true

# OpenStack Configuration
OS_AUTH_URL=http://127.0.0.1/identity/v3
OS_PROJECT_NAME=admin
OS_USERNAME=admin
OS_PASSWORD=nomoresecret
OS_USER_DOMAIN_NAME=Default
OS_PROJECT_DOMAIN_NAME=Default

# Monitoring Configuration
MONITOR_INTERVAL=30
MONITOR_TIMEOUT=10
MONITOR_RETRIES=3

# Alert Thresholds
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0

# Database
DATABASE_URL=sqlite:///./health_monitor.db

# Security
SECRET_KEY=your-secret-key-change-in-production
EOF
    echo "✅ .env file created from scratch"
fi

echo ""
echo "🔧 Automatic configuration with DevStack credentials..."

# Source DevStack credentials
if [ -f "/opt/stack/devstack/openrc" ]; then
    source /opt/stack/devstack/openrc admin admin
    
    # Update .env with real credentials
    sed -i "s|OS_AUTH_URL=.*|OS_AUTH_URL=$OS_AUTH_URL|g" .env
    sed -i "s|OS_PROJECT_NAME=.*|OS_PROJECT_NAME=$OS_PROJECT_NAME|g" .env
    sed -i "s|OS_USERNAME=.*|OS_USERNAME=$OS_USERNAME|g" .env
    sed -i "s|OS_PASSWORD=.*|OS_PASSWORD=$OS_PASSWORD|g" .env
    sed -i "s|OS_USER_DOMAIN_NAME=.*|OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME|g" .env
    sed -i "s|OS_PROJECT_DOMAIN_NAME=.*|OS_PROJECT_DOMAIN_NAME=$OS_PROJECT_DOMAIN_NAME|g" .env
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    
    echo "✅ DevStack credentials configured automatically"
else
    echo "⚠️ openrc file not found, configure credentials manually"
fi

echo ""
echo "📋 .env file contents:"
echo "====================="
cat .env

echo ""
echo "✅ Configuration completed!"
echo ""
echo "🎯 .env file created at: $(pwd)/.env"
echo "🔧 You can edit it with: nano .env"