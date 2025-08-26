import asyncio
import subprocess
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class CustomForensicAnalyzer:
    """
    Custom forensic analyzer that works without Volatility
    Provides real forensic analysis capabilities for the dashboard
    """
    
    def __init__(self, project_root: str = "/home/stack/plugin1/project"):
        self.project_root = Path(project_root)
        self.script_path = self.project_root / "custom-forensic-analysis.sh"
    
    async def analyze_memory_dump(self, dump_file_path: str) -> Dict[str, Any]:
        """
        Perform custom forensic analysis on a memory dump
        
        Args:
            dump_file_path: Path to the memory dump file
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Ensure the dump file exists
            if not os.path.exists(dump_file_path):
                return {
                    "error": f"Dump file not found: {dump_file_path}",
                    "status": "failed"
                }
            
            # Make sure the analysis script is executable
            await self._ensure_script_executable()
            
            # Run the custom forensic analysis
            process = await asyncio.create_subprocess_exec(
                str(self.script_path),
                dump_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "error": f"Analysis failed: {stderr.decode()}",
                    "status": "failed",
                    "exit_code": process.returncode
                }
            
            # Parse the JSON output from the analysis
            analysis_results = await self._parse_analysis_results(stdout.decode())
            
            return analysis_results
            
        except Exception as e:
            return {
                "error": f"Analysis exception: {str(e)}",
                "status": "failed"
            }
    
    async def _ensure_script_executable(self):
        """Make sure the analysis script is executable"""
        try:
            await asyncio.create_subprocess_exec(
                "chmod", "+x", str(self.script_path),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except Exception:
            pass  # Ignore errors, script might already be executable
    
    async def _parse_analysis_results(self, stdout: str) -> Dict[str, Any]:
        """
        Parse the analysis results from stdout and JSON file
        
        Args:
            stdout: Standard output from the analysis script
            
        Returns:
            Dict containing parsed analysis results
        """
        try:
            # Extract the analysis directory from stdout
            analysis_dir = None
            json_file = None
            
            for line in stdout.split('\n'):
                if "Analysis directory:" in line:
                    analysis_dir = line.split(":")[-1].strip()
                elif "JSON output for API:" in line:
                    json_file = line.split(":")[-1].strip()
            
            # Try to read the JSON output file
            if json_file and os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    json_results = json.load(f)
                
                # Add additional parsed information from analysis files
                if analysis_dir and os.path.exists(analysis_dir):
                    json_results.update(await self._parse_analysis_files(analysis_dir))
                
                # Add the stdout log for debugging
                json_results["analysis_log"] = stdout
                
                return json_results
            
            # Fallback: create basic results from stdout
            return {
                "status": "completed",
                "analysis_log": stdout,
                "analysis_directory": analysis_dir,
                "message": "Analysis completed but JSON output not found"
            }
            
        except Exception as e:
            return {
                "error": f"Failed to parse results: {str(e)}",
                "status": "failed",
                "raw_output": stdout
            }
    
    async def _parse_analysis_files(self, analysis_dir: str) -> Dict[str, Any]:
        """
        Parse individual analysis files to extract key information
        
        Args:
            analysis_dir: Directory containing analysis files
            
        Returns:
            Dict with parsed file contents
        """
        parsed_data = {}
        
        try:
            analysis_path = Path(analysis_dir)
            
            # Parse executables list
            executables_file = analysis_path / "executables.txt"
            if executables_file.exists():
                with open(executables_file, 'r') as f:
                    parsed_data["executables"] = [line.strip() for line in f.readlines()[:20]]  # Limit to 20
            
            # Parse IP addresses
            ips_file = analysis_path / "ip_addresses.txt"
            if ips_file.exists():
                with open(ips_file, 'r') as f:
                    parsed_data["ip_addresses"] = [line.strip() for line in f.readlines()[:50]]  # Limit to 50
            
            # Parse file info
            file_info = analysis_path / "file_info.txt"
            if file_info.exists():
                with open(file_info, 'r') as f:
                    parsed_data["file_type"] = f.read().strip()
            
            # Parse quick strings for interesting patterns
            quick_strings = analysis_path / "quick_strings.txt"
            if quick_strings.exists():
                with open(quick_strings, 'r') as f:
                    lines = f.readlines()
                    # Look for interesting patterns
                    parsed_data["sample_strings"] = {
                        "system_calls": [line.strip() for line in lines if any(syscall in line.lower() for syscall in ['open', 'read', 'write', 'connect', 'bind'])],
                        "file_paths": [line.strip() for line in lines if line.strip().startswith('/') and len(line.strip()) > 5],
                        "urls": [line.strip() for line in lines if any(proto in line.lower() for proto in ['http://', 'https://', 'ftp://'])]
                    }
                    
                    # Limit each category
                    for key in parsed_data["sample_strings"]:
                        parsed_data["sample_strings"][key] = parsed_data["sample_strings"][key][:10]
            
        except Exception as e:
            parsed_data["parsing_error"] = str(e)
        
        return parsed_data
    
    async def get_analysis_summary(self, dump_file_path: str) -> Dict[str, Any]:
        """
        Get a quick summary of analysis capabilities for a dump file
        
        Args:
            dump_file_path: Path to the memory dump file
            
        Returns:
            Dict containing analysis summary
        """
        try:
            if not os.path.exists(dump_file_path):
                return {
                    "error": "Dump file not found",
                    "status": "failed"
                }
            
            # Get basic file info
            file_stat = os.stat(dump_file_path)
            file_size = file_stat.st_size
            
            # Quick file type check
            process = await asyncio.create_subprocess_exec(
                "file", dump_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            file_type = stdout.decode().strip() if process.returncode == 0 else "Unknown"
            
            return {
                "status": "ready",
                "file_path": dump_file_path,
                "file_size": file_size,
                "file_size_human": self._human_readable_size(file_size),
                "file_type": file_type,
                "analysis_capabilities": [
                    "String extraction and analysis",
                    "Process executable detection",
                    "Network information extraction",
                    "File system structure analysis",
                    "Binary signature detection",
                    "Memory region mapping"
                ],
                "estimated_analysis_time": self._estimate_analysis_time(file_size)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _estimate_analysis_time(self, file_size: int) -> str:
        """Estimate analysis time based on file size"""
        if file_size < 100 * 1024 * 1024:  # < 100MB
            return "1-2 minutes"
        elif file_size < 500 * 1024 * 1024:  # < 500MB
            return "2-5 minutes"
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            return "5-10 minutes"
        else:  # > 1GB
            return "10-20 minutes"

# Example usage for testing
async def main():
    analyzer = CustomForensicAnalyzer()
    
    # Test with our existing dump
    dump_file = "./api_dumps/instance-00000003_20250823_200305/instance-00000003.dump"
    
    print("Getting analysis summary...")
    summary = await analyzer.get_analysis_summary(dump_file)
    print(json.dumps(summary, indent=2))
    
    print("\nStarting full analysis...")
    results = await analyzer.analyze_memory_dump(dump_file)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
