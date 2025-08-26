"""
Multi-Tool Forensic Analysis Service
Integrates multiple forensic tools for comprehensive memory analysis
"""

import asyncio
import json
import os
import subprocess
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import shutil

logger = logging.getLogger(__name__)

class MultiToolForensicAnalyzer:
    """
    Multi-tool forensic analyzer that combines multiple memory analysis tools
    """
    
    def __init__(self):
        self.supported_tools = {
            'binwalk': self._check_binwalk,
            'foremost': self._check_foremost,
            'bulk_extractor': self._check_bulk_extractor,
            'yara': self._check_yara,
            'strings': self._check_strings,
            'hexdump': self._check_hexdump
        }
        
    async def analyze_memory_dump(self, dump_path: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive forensic analysis using multiple tools
        
        Args:
            dump_path: Path to memory dump file
            tools: List of tools to use (None = all available)
            
        Returns:
            Dict containing analysis results from all tools
        """
        if not os.path.exists(dump_path):
            raise FileNotFoundError(f"Memory dump not found: {dump_path}")
            
        # Create analysis directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_dir = f"./multi_tool_analysis_{timestamp}"
        os.makedirs(analysis_dir, exist_ok=True)
        
        # Initialize results
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'dump_file': dump_path,
            'dump_size': os.path.getsize(dump_path),
            'analysis_directory': analysis_dir,
            'tools_used': [],
            'results': {},
            'summary': {},
            'errors': []
        }
        
        # Determine which tools to use
        if tools is None:
            tools_to_use = list(self.supported_tools.keys())
        else:
            tools_to_use = [tool for tool in tools if tool in self.supported_tools]
            
        # Check tool availability
        available_tools = []
        for tool in tools_to_use:
            if await self.supported_tools[tool]():
                available_tools.append(tool)
            else:
                results['errors'].append(f"Tool {tool} not available")
                
        logger.info(f"Using tools: {available_tools}")
        results['tools_used'] = available_tools
        
        # Run analysis with each tool
        analysis_tasks = []
        for tool in available_tools:
            task = self._run_tool_analysis(tool, dump_path, analysis_dir)
            analysis_tasks.append((tool, task))
            
        # Execute analyses
        for tool, task in analysis_tasks:
            try:
                tool_results = await task
                results['results'][tool] = tool_results
                logger.info(f"Completed {tool} analysis")
            except Exception as e:
                error_msg = f"Error in {tool} analysis: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['results'][tool] = {'error': str(e)}
                
        # Generate summary
        results['summary'] = await self._generate_summary(results)
        
        # Save results to JSON file
        json_output = os.path.join(analysis_dir, 'multi_tool_results.json')
        with open(json_output, 'w') as f:
            json.dump(results, f, indent=2)
            
        results['json_report'] = json_output
        
        return results
        
    async def _run_tool_analysis(self, tool: str, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run analysis for a specific tool"""
        
        if tool == 'binwalk':
            return await self._run_binwalk(dump_path, analysis_dir)
        elif tool == 'foremost':
            return await self._run_foremost(dump_path, analysis_dir)
        elif tool == 'bulk_extractor':
            return await self._run_bulk_extractor(dump_path, analysis_dir)
        elif tool == 'yara':
            return await self._run_yara(dump_path, analysis_dir)
        elif tool == 'strings':
            return await self._run_strings_analysis(dump_path, analysis_dir)
        elif tool == 'hexdump':
            return await self._run_hexdump_analysis(dump_path, analysis_dir)
        else:
            raise ValueError(f"Unsupported tool: {tool}")
            
    async def _run_binwalk(self, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run binwalk analysis"""
        output_dir = os.path.join(analysis_dir, 'binwalk_extracted')
        output_file = os.path.join(analysis_dir, 'binwalk_analysis.txt')
        
        cmd = [
            'binwalk', '-e', '-M', dump_path,
            '--dd=.*', f'--directory={output_dir}'
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Save output
            with open(output_file, 'w') as f:
                f.write(stdout.decode('utf-8', errors='ignore'))
                
            # Count extracted files
            extracted_files = []
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        extracted_files.append(os.path.join(root, file))
                        
            return {
                'output_file': output_file,
                'extracted_directory': output_dir,
                'extracted_files_count': len(extracted_files),
                'extracted_files': extracted_files[:20],  # First 20 files
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
            
    async def _run_foremost(self, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run foremost file carving"""
        output_dir = os.path.join(analysis_dir, 'foremost_carved')
        
        cmd = ['foremost', '-t', 'all', '-i', dump_path, '-o', output_dir]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            # Count carved files
            carved_files = []
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file != 'audit.txt':  # Skip foremost's audit file
                            carved_files.append(os.path.join(root, file))
                            
            # Read audit file if exists
            audit_file = os.path.join(output_dir, 'audit.txt')
            audit_content = ""
            if os.path.exists(audit_file):
                with open(audit_file, 'r') as f:
                    audit_content = f.read()
                    
            return {
                'output_directory': output_dir,
                'carved_files_count': len(carved_files),
                'carved_files': carved_files[:20],  # First 20 files
                'audit_content': audit_content,
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
            
    async def _run_bulk_extractor(self, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run bulk extractor analysis"""
        output_dir = os.path.join(analysis_dir, 'bulk_extractor_output')
        
        cmd = ['bulk_extractor', '-o', output_dir, dump_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            # Parse feature files
            features = {}
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    if filename.endswith('.txt') and filename != 'report.txt':
                        filepath = os.path.join(output_dir, filename)
                        if os.path.getsize(filepath) > 0:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                # Get first 10 lines for summary
                                lines = content.split('\n')[:10]
                                features[filename] = {
                                    'file_path': filepath,
                                    'line_count': len(content.split('\n')),
                                    'sample_content': lines
                                }
                                
            return {
                'output_directory': output_dir,
                'feature_files': features,
                'features_found': len(features),
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
            
    async def _run_yara(self, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run YARA pattern matching"""
        
        # Create YARA rules file
        rules_file = os.path.join(analysis_dir, 'memory_analysis.yar')
        yara_rules = '''
rule Linux_Kernel_Structures {
    meta:
        description = "Detect Linux kernel structures in memory"
        author = "Multi-Tool Forensic Analysis"
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
'''
        
        with open(rules_file, 'w') as f:
            f.write(yara_rules)
            
        output_file = os.path.join(analysis_dir, 'yara_matches.txt')
        
        cmd = ['yara', '-s', rules_file, dump_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Save matches
            matches_content = stdout.decode('utf-8', errors='ignore')
            with open(output_file, 'w') as f:
                f.write(matches_content)
                
            # Parse matches
            matches = []
            for line in matches_content.split('\n'):
                if line.strip():
                    matches.append(line.strip())
                    
            return {
                'rules_file': rules_file,
                'output_file': output_file,
                'matches_count': len(matches),
                'matches': matches[:50],  # First 50 matches
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
            
    async def _run_strings_analysis(self, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run advanced strings analysis"""
        output_file = os.path.join(analysis_dir, 'strings_advanced.txt')
        
        cmd = ['strings', '-a', '-t', 'x', '-n', '4', dump_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            strings_content = stdout.decode('utf-8', errors='ignore')
            with open(output_file, 'w') as f:
                f.write(strings_content)
                
            # Analyze patterns
            strings_lines = strings_content.split('\n')
            
            # Extract specific patterns
            ip_addresses = []
            file_paths = []
            commands = []
            
            for line in strings_lines:
                if len(line) > 10:  # Skip very short lines
                    # IP addresses
                    import re
                    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    if re.search(ip_pattern, line):
                        ip_addresses.append(line.strip())
                        
                    # File paths
                    if '/' in line and any(path in line for path in ['/bin', '/usr', '/etc', '/var', '/tmp']):
                        file_paths.append(line.strip())
                        
                    # Commands
                    if any(cmd in line.lower() for cmd in ['bash', 'sh', 'exec', 'cmd']):
                        commands.append(line.strip())
                        
            return {
                'output_file': output_file,
                'total_strings': len(strings_lines),
                'ip_addresses': ip_addresses[:20],
                'file_paths': file_paths[:20],
                'commands': commands[:20],
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
            
    async def _run_hexdump_analysis(self, dump_path: str, analysis_dir: str) -> Dict[str, Any]:
        """Run hexdump pattern analysis"""
        output_file = os.path.join(analysis_dir, 'hexdump_patterns.txt')
        
        # Analyze first 1MB only to avoid huge output
        cmd = ['hexdump', '-C', dump_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Read limited output (first 1000 lines)
            hex_lines = []
            line_count = 0
            while True:
                line = await process.stdout.readline()
                if not line or line_count > 1000:
                    break
                hex_lines.append(line.decode('utf-8', errors='ignore'))
                line_count += 1
                
            process.terminate()
            
            hex_content = ''.join(hex_lines)
            with open(output_file, 'w') as f:
                f.write(hex_content)
                
            # Look for specific signatures
            elf_headers = len([line for line in hex_lines if '7f 45 4c 46' in line])
            png_signatures = len([line for line in hex_lines if '89 50 4e 47' in line])
            zip_signatures = len([line for line in hex_lines if '50 4b 03 04' in line])
            
            return {
                'output_file': output_file,
                'lines_analyzed': len(hex_lines),
                'signatures_found': {
                    'elf_headers': elf_headers,
                    'png_signatures': png_signatures,
                    'zip_signatures': zip_signatures
                },
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
            
    async def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary"""
        summary = {
            'total_tools_used': len(results['tools_used']),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'key_findings': [],
            'file_artifacts': 0,
            'pattern_matches': 0,
            'analysis_complete': True
        }
        
        # Count successes and failures
        for tool, tool_results in results['results'].items():
            if 'error' in tool_results:
                summary['failed_analyses'] += 1
            else:
                summary['successful_analyses'] += 1
                
        # Extract key findings
        if 'foremost' in results['results'] and 'carved_files_count' in results['results']['foremost']:
            carved_count = results['results']['foremost']['carved_files_count']
            if carved_count > 0:
                summary['key_findings'].append(f"Carved {carved_count} files from memory")
                summary['file_artifacts'] += carved_count
                
        if 'yara' in results['results'] and 'matches_count' in results['results']['yara']:
            matches_count = results['results']['yara']['matches_count']
            if matches_count > 0:
                summary['key_findings'].append(f"Found {matches_count} YARA pattern matches")
                summary['pattern_matches'] += matches_count
                
        if 'strings' in results['results'] and 'total_strings' in results['results']['strings']:
            strings_count = results['results']['strings']['total_strings']
            summary['key_findings'].append(f"Extracted {strings_count} strings from memory")
            
        if 'binwalk' in results['results'] and 'extracted_files_count' in results['results']['binwalk']:
            extracted_count = results['results']['binwalk']['extracted_files_count']
            if extracted_count > 0:
                summary['key_findings'].append(f"Binwalk extracted {extracted_count} embedded files")
                summary['file_artifacts'] += extracted_count
                
        return summary
        
    # Tool availability checkers
    async def _check_binwalk(self) -> bool:
        """Check if binwalk is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'binwalk',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
            
    async def _check_foremost(self) -> bool:
        """Check if foremost is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'foremost',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
            
    async def _check_bulk_extractor(self) -> bool:
        """Check if bulk_extractor is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'bulk_extractor',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
            
    async def _check_yara(self) -> bool:
        """Check if yara is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'yara',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
            
    async def _check_strings(self) -> bool:
        """Check if strings is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'strings',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
            
    async def _check_hexdump(self) -> bool:
        """Check if hexdump is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'hexdump',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

# Global analyzer instance
multi_tool_analyzer = MultiToolForensicAnalyzer()

async def create_multi_tool_analysis(instance_name: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create comprehensive forensic analysis using multiple tools
    
    Args:
        instance_name: Name of the OpenStack instance
        tools: List of specific tools to use (None = all available)
        
    Returns:
        Dict containing comprehensive analysis results
    """
    try:
        # First create memory dump
        from .memory_dump import create_lime_dump
        
        dump_result = await create_lime_dump(instance_name)
        if 'error' in dump_result:
            return dump_result
            
        dump_path = dump_result['file_path']
        
        # Run multi-tool analysis
        analysis_results = await multi_tool_analyzer.analyze_memory_dump(dump_path, tools)
        
        # Combine results
        final_results = {
            'instance_name': instance_name,
            'memory_dump': dump_result,
            'multi_tool_analysis': analysis_results,
            'analysis_type': 'comprehensive_multi_tool',
            'timestamp': datetime.now().isoformat()
        }
        
        return final_results
        
    except Exception as e:
        logger.error(f"Multi-tool analysis failed for {instance_name}: {str(e)}")
        return {
            'error': f"Multi-tool analysis failed: {str(e)}",
            'instance_name': instance_name,
            'timestamp': datetime.now().isoformat()
        }
