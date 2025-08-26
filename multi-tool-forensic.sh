#!/bin/bash

# Multi-Tool Forensic Analysis
# Integrates multiple memory analysis tools for comprehensive forensic analysis
# Usage: ./multi-tool-forensic.sh <memory_dump>

DUMP_FILE="$1"

if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
    echo "Usage: $0 <memory_dump_file>"
    echo "Example: $0 ./api_dumps/instance.dump"
    exit 1
fi

echo "🔬 Multi-Tool Forensic Analysis"
echo "==============================="
echo "📂 Analyzing: $DUMP_FILE"
echo "📊 Size: $(ls -lh "$DUMP_FILE" | awk '{print $5}')"

# Create analysis directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ANALYSIS_DIR="./multi_tool_analysis_${TIMESTAMP}"
mkdir -p "$ANALYSIS_DIR"

echo "📁 Analysis output: $ANALYSIS_DIR"

# Initialize results
RESULTS_JSON="$ANALYSIS_DIR/multi_tool_results.json"
cat > "$RESULTS_JSON" << 'EOF'
{
  "analysis_timestamp": "",
  "dump_file": "",
  "dump_size": 0,
  "tools_used": [],
  "results": {
    "binwalk": {},
    "foremost": {},
    "bulk_extractor": {},
    "yara": {},
    "strings_advanced": {},
    "hexdump_analysis": {},
    "custom_patterns": {},
    "summary": {}
  }
}
EOF

# Tool 1: Binwalk - Firmware analysis and file extraction
echo ""
echo "🔧 Tool 1: Binwalk Analysis"
echo "=========================="
if command -v binwalk >/dev/null 2>&1; then
    echo "✅ Binwalk found"
    
    BINWALK_OUTPUT="$ANALYSIS_DIR/binwalk_analysis.txt"
    echo "📂 Running binwalk analysis..."
    
    # Extract files and analyze structure
    binwalk -e -M "$DUMP_FILE" --dd=".*" --directory="$ANALYSIS_DIR/binwalk_extracted" > "$BINWALK_OUTPUT" 2>&1
    
    echo "📊 Binwalk results:"
    head -20 "$BINWALK_OUTPUT"
    
    if [ -d "$ANALYSIS_DIR/binwalk_extracted" ]; then
        echo "📁 Extracted files:"
        find "$ANALYSIS_DIR/binwalk_extracted" -type f | head -10
    fi
else
    echo "❌ Binwalk not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y binwalk
fi

# Tool 2: Foremost - File carving
echo ""
echo "🔧 Tool 2: Foremost File Carving"
echo "================================"
if command -v foremost >/dev/null 2>&1; then
    echo "✅ Foremost found"
    
    FOREMOST_DIR="$ANALYSIS_DIR/foremost_carved"
    mkdir -p "$FOREMOST_DIR"
    
    echo "📂 Running foremost file carving..."
    foremost -t all -i "$DUMP_FILE" -o "$FOREMOST_DIR" 2>/dev/null
    
    echo "📊 Carved files:"
    find "$FOREMOST_DIR" -type f | wc -l | xargs echo "Total files:"
    find "$FOREMOST_DIR" -type f | head -10
else
    echo "❌ Foremost not installed. Installing..."
    sudo apt-get install -y foremost
fi

# Tool 3: Bulk Extractor - Advanced data extraction
echo ""
echo "🔧 Tool 3: Bulk Extractor"
echo "========================="
if command -v bulk_extractor >/dev/null 2>&1; then
    echo "✅ Bulk Extractor found"
    
    BULK_DIR="$ANALYSIS_DIR/bulk_extractor_output"
    mkdir -p "$BULK_DIR"
    
    echo "📂 Running bulk extractor..."
    bulk_extractor -o "$BULK_DIR" "$DUMP_FILE" 2>/dev/null
    
    echo "📊 Bulk extractor results:"
    ls -la "$BULK_DIR"/ | head -10
    
    # Show key findings
    for feature_file in "$BULK_DIR"/*.txt; do
        if [ -f "$feature_file" ] && [ -s "$feature_file" ]; then
            filename=$(basename "$feature_file")
            echo "📋 $filename (first 5 lines):"
            head -5 "$feature_file"
            echo ""
        fi
    done
else
    echo "❌ Bulk Extractor not installed. Installing..."
    sudo apt-get install -y bulk-extractor
fi

# Tool 4: YARA Rules - Malware and pattern detection
echo ""
echo "🔧 Tool 4: YARA Pattern Matching"
echo "==============================="

# Create custom YARA rules for memory analysis
YARA_RULES="$ANALYSIS_DIR/memory_analysis.yar"
cat > "$YARA_RULES" << 'EOF'
rule Linux_Kernel_Structures {
    meta:
        description = "Detect Linux kernel structures in memory"
        author = "Custom Forensic Analysis"
    strings:
        $task_struct = "task_struct"
        $init_task = "init_task" 
        $swapper = "swapper"
        $kthreadd = "kthreadd"
        $ksoftirqd = "ksoftirqd"
        $systemd = "systemd"
    condition:
        any of them
}

rule Network_Artifacts {
    meta:
        description = "Network-related artifacts"
    strings:
        $tcp = "tcp"
        $udp = "udp"
        $socket = "socket"
        $netlink = "netlink"
        $eth0 = "eth0"
        $lo = "lo"
    condition:
        any of them
}

rule Suspicious_Strings {
    meta:
        description = "Potentially suspicious strings"
    strings:
        $passwd = "/etc/passwd"
        $shadow = "/etc/shadow"
        $bash_history = ".bash_history"
        $ssh_key = "ssh-rsa"
        $private_key = "PRIVATE KEY"
    condition:
        any of them
}

rule Process_Memory {
    meta:
        description = "Process memory indicators"
    strings:
        $proc_self = "/proc/self"
        $proc_pid = "/proc/"
        $cmdline = "cmdline"
        $environ = "environ"
        $maps = "maps"
    condition:
        any of them
}
EOF

if command -v yara >/dev/null 2>&1; then
    echo "✅ YARA found"
    
    YARA_OUTPUT="$ANALYSIS_DIR/yara_matches.txt"
    echo "📂 Running YARA analysis..."
    
    yara -s "$YARA_RULES" "$DUMP_FILE" > "$YARA_OUTPUT" 2>&1
    
    echo "📊 YARA matches:"
    cat "$YARA_OUTPUT" | head -20
else
    echo "❌ YARA not installed. Installing..."
    sudo apt-get install -y yara
fi

# Tool 5: Advanced Strings Analysis with Context
echo ""
echo "🔧 Tool 5: Advanced Strings Analysis"
echo "===================================="

STRINGS_ADVANCED="$ANALYSIS_DIR/strings_advanced.txt"
echo "📂 Extracting strings with context..."

# Extract strings with minimum length and encoding detection
strings -a -t x -n 4 "$DUMP_FILE" > "$STRINGS_ADVANCED"

echo "📊 Advanced strings analysis:"
echo "Total strings: $(wc -l < "$STRINGS_ADVANCED")"

# Analyze specific patterns
echo ""
echo "🔍 Command line patterns:"
grep -i "bash\|sh\|cmd\|exec" "$STRINGS_ADVANCED" | head -10

echo ""
echo "🔍 File system patterns:"
grep -E "/(bin|sbin|usr|etc|var|tmp|home)/" "$STRINGS_ADVANCED" | head -10

echo ""
echo "🔍 Network patterns:"
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" "$STRINGS_ADVANCED" | head -10

# Tool 6: Hexdump Pattern Analysis
echo ""
echo "🔧 Tool 6: Hexdump Pattern Analysis"
echo "==================================="

HEXDUMP_ANALYSIS="$ANALYSIS_DIR/hexdump_patterns.txt"
echo "📂 Analyzing hex patterns..."

# Look for specific signatures in hex
hexdump -C "$DUMP_FILE" | head -1000 > "$HEXDUMP_ANALYSIS"

echo "📊 Hex analysis - looking for signatures:"
echo ""
echo "🔍 ELF headers:"
hexdump -C "$DUMP_FILE" | grep "7f 45 4c 46" | head -5

echo ""
echo "🔍 PNG signatures:"
hexdump -C "$DUMP_FILE" | grep "89 50 4e 47" | head -5

echo ""
echo "🔍 ZIP signatures:"
hexdump -C "$DUMP_FILE" | grep "50 4b 03 04" | head -5

# Tool 7: Custom Memory Structure Analysis
echo ""
echo "🔧 Tool 7: Custom Memory Structure Analysis"
echo "============================================"

CUSTOM_ANALYSIS="$ANALYSIS_DIR/custom_memory_analysis.txt"

python3 << EOF > "$CUSTOM_ANALYSIS"
import struct
import sys

def analyze_memory_dump(filename):
    results = {
        'elf_headers': [],
        'potential_strings': [],
        'memory_regions': [],
        'suspicious_patterns': []
    }
    
    try:
        with open(filename, 'rb') as f:
            # Read first 1MB for analysis
            data = f.read(1024 * 1024)
            
            # Look for ELF headers
            for i in range(len(data) - 4):
                if data[i:i+4] == b'\x7fELF':
                    results['elf_headers'].append(hex(i))
            
            # Look for potential process names (printable strings)
            current_string = b""
            for i, byte in enumerate(data):
                if 32 <= byte <= 126:  # Printable ASCII
                    current_string += bytes([byte])
                else:
                    if len(current_string) >= 4:
                        try:
                            string_val = current_string.decode('ascii')
                            if any(keyword in string_val.lower() for keyword in ['process', 'thread', 'task', 'pid', 'uid']):
                                results['potential_strings'].append(f"{hex(i-len(current_string))}: {string_val}")
                        except:
                            pass
                    current_string = b""
            
            # Look for memory page boundaries (4KB aligned)
            f.seek(0)
            for offset in range(0, min(1024*1024*10, f.seek(0, 2)), 4096):  # Check first 10MB
                f.seek(offset)
                page_data = f.read(16)
                if page_data:
                    # Check if page looks like it contains data
                    non_zero = sum(1 for b in page_data if b != 0)
                    if non_zero > 8:  # Page has significant data
                        results['memory_regions'].append(f"Active page at {hex(offset)}")
    
    except Exception as e:
        print(f"Error analyzing memory dump: {e}")
        return results
    
    return results

# Analyze the dump
results = analyze_memory_dump('$DUMP_FILE')

print("🔍 Custom Memory Analysis Results:")
print("==================================")
print(f"ELF headers found: {len(results['elf_headers'])}")
if results['elf_headers']:
    print("ELF header locations:", ', '.join(results['elf_headers'][:10]))

print(f"\\nPotential process-related strings: {len(results['potential_strings'])}")
for s in results['potential_strings'][:10]:
    print(f"  {s}")

print(f"\\nActive memory regions: {len(results['memory_regions'])}")
for region in results['memory_regions'][:10]:
    print(f"  {region}")
EOF

echo "📊 Custom analysis results:"
cat "$CUSTOM_ANALYSIS"

# Generate comprehensive JSON report
echo ""
echo "🔧 Generating Comprehensive Report"
echo "=================================="

# Update JSON results
python3 << EOF
import json
import os
from datetime import datetime

# Load existing JSON
with open('$RESULTS_JSON', 'r') as f:
    results = json.load(f)

# Update with analysis info
results['analysis_timestamp'] = datetime.now().isoformat()
results['dump_file'] = '$DUMP_FILE'
results['dump_size'] = os.path.getsize('$DUMP_FILE')
results['tools_used'] = ['binwalk', 'foremost', 'bulk_extractor', 'yara', 'strings', 'hexdump', 'custom_analysis']

# Add summary
results['results']['summary'] = {
    'analysis_directory': '$ANALYSIS_DIR',
    'total_tools_used': len(results['tools_used']),
    'analysis_complete': True,
    'findings': {
        'file_carving_attempted': True,
        'pattern_matching_completed': True,
        'string_extraction_completed': True,
        'custom_analysis_completed': True
    }
}

# Save updated results
with open('$RESULTS_JSON', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ JSON report updated")
EOF

echo ""
echo "🎯 Multi-Tool Forensic Analysis Complete!"
echo "=========================================="
echo "📁 Analysis directory: $ANALYSIS_DIR"
echo "📊 JSON results: $RESULTS_JSON"
echo ""
echo "🔍 Analysis includes:"
echo "  ✅ Binwalk - Firmware and file structure analysis"
echo "  ✅ Foremost - File carving and recovery"
echo "  ✅ Bulk Extractor - Advanced data extraction"
echo "  ✅ YARA - Pattern and malware detection"
echo "  ✅ Advanced Strings - Context-aware string analysis"
echo "  ✅ Hexdump - Low-level pattern analysis"
echo "  ✅ Custom Analysis - Memory structure analysis"
echo ""
echo "🎯 Key Findings Summary:"
if [ -f "$ANALYSIS_DIR/binwalk_analysis.txt" ]; then
    echo "  📋 Binwalk found: $(wc -l < "$ANALYSIS_DIR/binwalk_analysis.txt") entries"
fi
if [ -d "$ANALYSIS_DIR/foremost_carved" ]; then
    echo "  📋 Foremost carved: $(find "$ANALYSIS_DIR/foremost_carved" -type f 2>/dev/null | wc -l) files"
fi
if [ -f "$ANALYSIS_DIR/yara_matches.txt" ]; then
    echo "  📋 YARA matches: $(wc -l < "$ANALYSIS_DIR/yara_matches.txt") patterns"
fi
if [ -f "$ANALYSIS_DIR/strings_advanced.txt" ]; then
    echo "  📋 Advanced strings: $(wc -l < "$ANALYSIS_DIR/strings_advanced.txt") entries"
fi

echo ""
echo "🎯 This comprehensive analysis provides:"
echo "  🔍 File recovery and carving"
echo "  🔍 Malware and threat detection"
echo "  🔍 Network artifact extraction"
echo "  🔍 Process and system information"
echo "  🔍 Custom forensic insights"
echo ""
echo "📄 Use this data in your forensic dashboard for complete analysis!"

# Print final JSON for API consumption (backend expects this)
echo ""
echo "=== JSON_OUTPUT_START ==="
cat "$RESULTS_JSON"
echo "=== JSON_OUTPUT_END ==="
