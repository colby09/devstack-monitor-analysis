#!/bin/bash
# Complete rebuild and restart script for DevStack Monitor and Analysis Plugin

echo "🔄 Complete Rebuild and Restart"
echo "==============================="

# Go to the project directory
cd /opt/stack/devstack-monitor-analysis

# 1. Stop the server
echo "📋 1. Stopping server..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# 2. Clean and rebuild frontend
echo "📋 2. Rebuilding frontend..."
rm -rf dist/
npm run build

# 3. Verify build
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend built successfully:"
ls -la dist/

# 4. Verify index.html content
echo "📄 index.html content:"
head -5 dist/index.html

# 5. Restart server
echo "📋 3. Restarting server..."
cd backend
source ../.venv/bin/activate

echo "🚀 Starting server with updated frontend..."
python main.py &

# 6. Wait for startup
sleep 3

# 7. Test
echo "📋 4. Final test..."
echo "🌐 API Test:"
curl -s http://localhost:8080/health | python3 -m json.tool

echo ""
echo "🌐 Frontend Test:"
if curl -s http://localhost:8080/ | grep -q "DevStack Monitor and Analysis"; then
    echo "✅ Frontend loads correctly!"
else
    echo "❌ Frontend still not loading"
    echo "📄 Server response:"
    curl -s http://localhost:8080/ | head -10
fi

echo ""
echo "🎯 RESULT:"
echo "=========="
echo "✅ Server restarted with updated frontend"
echo "🌐 Dashboard: http://localhost:8080"
echo "📊 Metrics: http://localhost:8080/api/metrics/summary"
echo "📚 API Docs: http://localhost:8080/docs"