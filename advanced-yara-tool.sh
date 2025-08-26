#!/bin/bash

# Advanced YARA Analysis Tool for Memory Dumps
# Focuses on credentials, system info, and process data
# Usage: ./advanced-yara-tool.sh <dump_file>

DUMP_FILE="$1"

if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
    echo "Usage: $0 <memory_dump_file>"
    echo "Example: $0 ./simple_dumps/test_cirros2.raw"
    exit 1
fi

echo "🔍 Advanced YARA Analysis Tool"
echo "=============================="
echo "📂 Analyzing: $DUMP_FILE"
echo "📊 Size: $(ls -lh "$DUMP_FILE" | awk '{print $5}')"

# Create analysis directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ANALYSIS_DIR="./advanced_yara_analysis_${TIMESTAMP}"
mkdir -p "$ANALYSIS_DIR"

echo "📁 Analysis output: $ANALYSIS_DIR"

# Create advanced YARA rules
YARA_RULES="$ANALYSIS_DIR/advanced_forensic.yar"
cat > "$YARA_RULES" << 'EOF'
rule CirrOS_Credentials {
    meta:
        description = "CirrOS system credentials and login information"
        author = "Advanced Forensic Analysis"
        severity = "high"
    strings:
        $login_msg = "login as 'cirros' user"
        $password = "default password:"
        $gocubsgo = "gocubsgo"
        $sudo_msg = "use 'sudo' for root"
        $sudoers = "cirros ALL=(ALL) NOPASSWD:ALL"
        $cirros_user = "cirros:"
    condition:
        any of them
}

rule System_Configuration {
    meta:
        description = "System configuration files and settings"
        author = "Advanced Forensic Analysis"
    strings:
        $passwd_file = "/etc/passwd"
        $shadow_file = "/etc/shadow"
        $sudoers_file = "/etc/sudoers"
        $hosts_file = "/etc/hosts"
        $fstab = "/etc/fstab"
        $issue = "/etc/issue"
        $hostname = "/etc/hostname"
    condition:
        any of them
}

rule Process_Memory_Maps {
    meta:
        description = "Process memory mapping information"
        author = "Advanced Forensic Analysis"
    strings:
        $proc_maps = "/proc/"
        $maps_suffix = "/maps"
        $cmdline = "/cmdline"
        $environ = "/environ"
        $status = "/status"
        $mem = "/mem"
    condition:
        2 of them
}

rule Network_Information {
    meta:
        description = "Network configuration and connection data"
        author = "Advanced Forensic Analysis"
    strings:
        $eth0 = "eth0"
        $lo = "lo"
        $ifconfig = "ifconfig"
        $netstat = "netstat"
        $route = "route"
        $iptables = "iptables"
        $ssh = "ssh"
        $tcp = "tcp"
        $udp = "udp"
    condition:
        any of them
}

rule SSH_Keys_And_Auth {
    meta:
        description = "SSH keys and authentication data"
        author = "Advanced Forensic Analysis"
        severity = "high"
    strings:
        $ssh_rsa = "ssh-rsa"
        $ssh_dsa = "ssh-dsa"
        $ssh_ed25519 = "ssh-ed25519"
        $private_key = "-----BEGIN PRIVATE KEY-----"
        $rsa_private = "-----BEGIN RSA PRIVATE KEY-----"
        $authorized_keys = "authorized_keys"
        $known_hosts = "known_hosts"
    condition:
        any of them
}

rule Command_History {
    meta:
        description = "Command history and shell activity"
        author = "Advanced Forensic Analysis"
    strings:
        $bash_history = ".bash_history"
        $history = "history"
        $sudo_cmd = "sudo "
        $su_cmd = "su "
        $passwd_cmd = "passwd"
        $useradd = "useradd"
        $usermod = "usermod"
    condition:
        any of them
}

rule System_Processes {
    meta:
        description = "System processes and daemons"
        author = "Advanced Forensic Analysis"
    strings:
        $init = "init"
        $systemd = "systemd"
        $kthreadd = "kthreadd"
        $ksoftirqd = "ksoftirqd"
        $migration = "migration"
        $rcu_gp = "rcu_gp"
        $watchdog = "watchdog"
        $sshd = "sshd"
        $cron = "cron"
        $dhcp = "dhcp"
    condition:
        any of them
}

rule File_System_Info {
    meta:
        description = "File system and mount information"
        author = "Advanced Forensic Analysis"
    strings:
        $root_fs = "/"
        $tmp_fs = "/tmp"
        $var_fs = "/var"
        $home_fs = "/home"
        $proc_fs = "/proc"
        $sys_fs = "/sys"
        $dev_fs = "/dev"
        $mount = "mount"
        $umount = "umount"
        $ext2 = "ext2"
        $ext3 = "ext3"
        $ext4 = "ext4"
    condition:
        any of them
}

rule Potential_Malware {
    meta:
        description = "Potential malware indicators"
        author = "Advanced Forensic Analysis"
        severity = "critical"
    strings:
        $wget = "wget"
        $curl = "curl"
        $nc = "nc "
        $netcat = "netcat"
        $base64 = "base64"
        $chmod_777 = "chmod 777"
        $tmp_script = "/tmp/"
        $dev_null = "/dev/null"
        $nohup = "nohup"
        $background = " &"
    condition:
        3 of them
}
EOF

echo "📝 Created advanced YARA rules: $YARA_RULES"

# Run YARA analysis
OUTPUT_FILE="$ANALYSIS_DIR/advanced_matches.txt"
echo ""
echo "🔧 Running Advanced YARA Analysis..."
echo "===================================="

yara -s "$YARA_RULES" "$DUMP_FILE" > "$OUTPUT_FILE" 2>&1

echo "📊 Analysis Results:"
echo "==================="

# Process and categorize results
for rule in "CirrOS_Credentials" "System_Configuration" "Process_Memory_Maps" "Network_Information" "SSH_Keys_And_Auth" "Command_History" "System_Processes" "File_System_Info" "Potential_Malware"; do
    echo ""
    echo "🔍 $rule:"
    echo "$(printf '=%.0s' {1..50})"
    
    matches=$(grep "^$rule " "$OUTPUT_FILE" | wc -l)
    echo "📈 Total matches: $matches"
    
    if [ $matches -gt 0 ]; then
        echo "📋 Sample matches:"
        grep "^$rule " "$OUTPUT_FILE" | head -10 | while read line; do
            echo "  $line"
        done
        
        if [ $matches -gt 10 ]; then
            echo "  ... and $((matches - 10)) more matches"
        fi
    else
        echo "  No matches found"
    fi
done

# Extract specific credential information
echo ""
echo "🔐 Credential Extraction"
echo "======================="

# Search for cirros credentials specifically
echo "🔍 CirrOS Login Information:"
grep -i "cirros.*password\|password.*cirros\|gocubsgo" "$OUTPUT_FILE" | head -5

echo ""
echo "🔍 Sudo Configuration:"
grep -i "cirros.*nopasswd\|sudoers" "$OUTPUT_FILE" | head -5

# Generate summary report
SUMMARY_FILE="$ANALYSIS_DIR/forensic_summary.txt"
cat > "$SUMMARY_FILE" << EOF
Advanced YARA Forensic Analysis Summary
======================================
Timestamp: $(date)
Dump File: $DUMP_FILE
Analysis Directory: $ANALYSIS_DIR

Rule Match Summary:
- CirrOS Credentials: $(grep "^CirrOS_Credentials " "$OUTPUT_FILE" | wc -l) matches
- System Configuration: $(grep "^System_Configuration " "$OUTPUT_FILE" | wc -l) matches  
- Process Memory Maps: $(grep "^Process_Memory_Maps " "$OUTPUT_FILE" | wc -l) matches
- Network Information: $(grep "^Network_Information " "$OUTPUT_FILE" | wc -l) matches
- SSH Keys/Auth: $(grep "^SSH_Keys_And_Auth " "$OUTPUT_FILE" | wc -l) matches
- Command History: $(grep "^Command_History " "$OUTPUT_FILE" | wc -l) matches
- System Processes: $(grep "^System_Processes " "$OUTPUT_FILE" | wc -l) matches
- File System Info: $(grep "^File_System_Info " "$OUTPUT_FILE" | wc -l) matches
- Potential Malware: $(grep "^Potential_Malware " "$OUTPUT_FILE" | wc -l) matches

Total Pattern Matches: $(wc -l < "$OUTPUT_FILE")

Key Findings:
$(if grep -q "gocubsgo" "$OUTPUT_FILE"; then echo "- CirrOS default password found in memory"; fi)
$(if grep -q "NOPASSWD" "$OUTPUT_FILE"; then echo "- Sudo configuration without password found"; fi)
$(if grep -q "ssh-rsa\|ssh-dsa" "$OUTPUT_FILE"; then echo "- SSH keys detected in memory"; fi)
$(if grep -q "/etc/passwd\|/etc/shadow" "$OUTPUT_FILE"; then echo "- System authentication files referenced"; fi)
EOF

echo ""
echo "📄 Summary Report Generated: $SUMMARY_FILE"
cat "$SUMMARY_FILE"

# Generate JSON output for API integration
JSON_OUTPUT="$ANALYSIS_DIR/advanced_yara_results.json"
python3 << EOF > "$JSON_OUTPUT"
import json
import os
from datetime import datetime

# Read YARA matches
matches = {}
rule_counts = {}

with open('$OUTPUT_FILE', 'r') as f:
    for line in f:
        if line.strip():
            parts = line.strip().split(' ', 1)
            if len(parts) >= 2:
                rule_name = parts[0]
                match_info = parts[1]
                
                if rule_name not in matches:
                    matches[rule_name] = []
                    rule_counts[rule_name] = 0
                
                matches[rule_name].append(match_info)
                rule_counts[rule_name] += 1

# Create JSON structure
results = {
    "analysis_timestamp": datetime.now().isoformat(),
    "dump_file": "$DUMP_FILE",
    "analysis_directory": "$ANALYSIS_DIR",
    "yara_rules_file": "$YARA_RULES",
    "total_matches": sum(rule_counts.values()),
    "rule_summary": rule_counts,
    "detailed_matches": matches,
    "key_findings": {
        "credentials_found": rule_counts.get("CirrOS_Credentials", 0) > 0,
        "system_config_found": rule_counts.get("System_Configuration", 0) > 0,
        "process_maps_found": rule_counts.get("Process_Memory_Maps", 0) > 0,
        "network_info_found": rule_counts.get("Network_Information", 0) > 0,
        "ssh_keys_found": rule_counts.get("SSH_Keys_And_Auth", 0) > 0,
        "potential_malware": rule_counts.get("Potential_Malware", 0) > 0
    }
}

print(json.dumps(results, indent=2))
EOF

echo ""
echo "🎯 Advanced YARA Analysis Complete!"
echo "==================================="
echo "📁 Analysis Directory: $ANALYSIS_DIR"
echo "📊 Detailed Results: $OUTPUT_FILE"
echo "📄 Summary Report: $SUMMARY_FILE"
echo "📄 JSON Results: $JSON_OUTPUT"

echo ""
echo "🔍 Key Insights:"
echo "- Process memory maps detected: $(grep "^Process_Memory_Maps " "$OUTPUT_FILE" | wc -l) locations"
echo "- Credential patterns found: $(grep "^CirrOS_Credentials " "$OUTPUT_FILE" | wc -l) matches"
echo "- System configuration references: $(grep "^System_Configuration " "$OUTPUT_FILE" | wc -l) matches"

echo ""
echo "🎯 This advanced analysis provides deeper forensic insights!"
echo "Ready for integration into your forensic dashboard."

# Print final JSON for API consumption (backend expects this)
echo ""
echo "=== JSON_OUTPUT_START ==="
cat "$JSON_OUTPUT"
echo "=== JSON_OUTPUT_END ==="
