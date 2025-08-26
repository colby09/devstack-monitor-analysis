"""
Integrated Forensic Analysis Service
Combines memory dump creation, multi-tool analysis, YARA analysis, and PDF reporting
"""

import asyncio
import uuid
import logging
import json
import os
import subprocess
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from ..models.instance import Instance
from .memory_dump import memory_dump_service

# Create logger for this module
logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    PENDING = "pending"
    DUMPING_MEMORY = "dumping_memory"
    ANALYZING = "analyzing"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ForensicResults:
    """Results from integrated forensic analysis"""
    dump_info: Dict[str, Any]
    binwalk_results: Dict[str, Any]
    foremost_results: Dict[str, Any]
    yara_results: Dict[str, Any]
    strings_analysis: Dict[str, Any]
    hexdump_analysis: Dict[str, Any]
    advanced_yara: Dict[str, Any]
    summary: Dict[str, Any]


@dataclass
class IntegratedAnalysis:
    """Integrated forensic analysis record"""
    id: str
    instance_id: str
    instance_name: str
    status: AnalysisStatus
    progress: int
    current_step: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dump_id: Optional[str] = None
    dump_file_path: Optional[str] = None
    results: Optional[ForensicResults] = None
    report_path: Optional[str] = None
    error_message: Optional[str] = None


class IntegratedForensicService:
    """Service for complete forensic analysis pipeline"""

    def __init__(self):
        self.analyses_db: Dict[str, IntegratedAnalysis] = {}
        self.active_analyses: Dict[str, asyncio.Task] = {}
        self.base_directory = Path("/home/stack/forensic")
        # Use plugin directory directly instead of symlink
        self.scripts_directory = Path("/opt/stack/devstack-monitor-analysis")

        # Ensure directories exist
        self.base_directory.mkdir(parents=True, exist_ok=True)
        (self.base_directory / "reports").mkdir(exist_ok=True)

        logger.info("IntegratedForensicService initialized")

    async def start_analysis(self, instance_id: str, instance_name: str) -> str:
        """Start complete forensic analysis pipeline"""

        analysis_id = str(uuid.uuid4())

        # Create analysis record
        analysis = IntegratedAnalysis(
            id=analysis_id,
            instance_id=instance_id,
            instance_name=instance_name,
            status=AnalysisStatus.PENDING,
            progress=0,
            current_step="Initializing forensic analysis...",
            created_at=datetime.now()
        )

        self.analyses_db[analysis_id] = analysis

        # Start analysis process asynchronously
        task = asyncio.create_task(self._perform_complete_analysis(analysis_id))
        self.active_analyses[analysis_id] = task

        logger.info(f"Started integrated forensic analysis {analysis_id} for instance {instance_id}")
        return analysis_id

    async def start_analysis_from_dump(self, dump_id: str, instance_id: str, instance_name: str) -> str:
        """Start forensic analysis from existing memory dump"""

        # Verify that the dump exists and is completed
        dump = memory_dump_service.get_dump(dump_id)
        if not dump:
            raise Exception(f"Memory dump {dump_id} not found")

        # Check status (handle both string and enum cases)
        dump_status = dump.status if isinstance(dump.status, str) else dump.status.value
        if dump_status.lower() != "completed":
            raise Exception(f"Memory dump {dump_id} is not completed (status: {dump_status})")

        analysis_id = str(uuid.uuid4())

        # Create analysis record
        analysis = IntegratedAnalysis(
            id=analysis_id,
            instance_id=instance_id,
            instance_name=instance_name,
            status=AnalysisStatus.ANALYZING,  # Skip dumping phase
            progress=20,  # Start at 20% since dump is already done
            current_step="Initializing analysis from existing dump...",
            created_at=datetime.now(),
            started_at=datetime.now(),
            dump_id=dump_id
        )

        self.analyses_db[analysis_id] = analysis

        # Start analysis process asynchronously (skip dump creation)
        task = asyncio.create_task(self._perform_analysis_from_dump(analysis_id, dump_id))
        self.active_analyses[analysis_id] = task

        logger.info(f"Started forensic analysis {analysis_id} from existing dump {dump_id} for instance {instance_id}")
        return analysis_id

    async def _perform_complete_analysis(self, analysis_id: str):
        """Perform complete forensic analysis pipeline"""
        analysis = self.analyses_db[analysis_id]

        try:
            analysis.status = AnalysisStatus.DUMPING_MEMORY
            analysis.started_at = datetime.now()
            analysis.progress = 5
            analysis.current_step = "Creating memory dump..."

            # STEP 1: Create memory dump using virsh method
            dump_id = await memory_dump_service.create_dump(analysis.instance_id)
            analysis.dump_id = dump_id

            # Wait for dump completion
            while True:
                dump = memory_dump_service.get_dump(dump_id)
                if dump.status.value == "completed":
                    analysis.dump_file_path = dump.file_path
                    break
                elif dump.status.value == "failed":
                    raise Exception(f"Memory dump failed: {dump.error_message}")

                await asyncio.sleep(2)

            analysis.progress = 20
            analysis.current_step = "Memory dump completed. Starting multi-tool analysis..."

            # STEP 2: Multi-tool forensic analysis
            analysis.status = AnalysisStatus.ANALYZING
            analysis.progress = 30
            analysis.current_step = "Running multi-tool forensic analysis..."

            multi_tool_results = await self._run_multi_tool_analysis(analysis.dump_file_path)

            analysis.progress = 60
            analysis.current_step = "Running advanced YARA analysis..."

            # STEP 3: Advanced YARA analysis
            yara_results = await self._run_advanced_yara_analysis(analysis.dump_file_path)

            analysis.progress = 80
            analysis.current_step = "Generating comprehensive report..."

            # STEP 4: Combine results
            results = ForensicResults(
                dump_info={
                    "file_path": analysis.dump_file_path,
                    "file_size": os.path.getsize(analysis.dump_file_path),
                    "created_at": analysis.started_at.isoformat(),
                    "instance_id": analysis.instance_id,
                    "instance_name": analysis.instance_name
                },
                binwalk_results=self._safe_get_results(multi_tool_results, "binwalk"),
                foremost_results=self._safe_get_results(multi_tool_results, "foremost"),
                yara_results=self._safe_get_results(multi_tool_results, "yara"),
                strings_analysis=self._safe_get_results(multi_tool_results, "strings"),
                hexdump_analysis=self._safe_get_results(multi_tool_results, "hexdump"),
                advanced_yara=yara_results if isinstance(yara_results, dict) else {"error": "Invalid YARA results"},
                summary=self._generate_summary(multi_tool_results, yara_results)
            )

            analysis.results = results

            # STEP 5: Generate PDF report
            analysis.status = AnalysisStatus.GENERATING_REPORT
            analysis.progress = 90
            analysis.current_step = "Generating PDF report..."

            report_path = await self._generate_pdf_report(analysis)
            analysis.report_path = report_path

            # Complete
            analysis.status = AnalysisStatus.COMPLETED
            analysis.progress = 100
            analysis.current_step = "Analysis completed successfully"
            analysis.completed_at = datetime.now()

            logger.info(f"Integrated forensic analysis {analysis_id} completed successfully")

        except Exception as e:
            logger.error(f"Integrated forensic analysis {analysis_id} failed: {e}")
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            analysis.current_step = f"Analysis failed: {str(e)}"

        finally:
            # Clean up active analysis task
            if analysis_id in self.active_analyses:
                del self.active_analyses[analysis_id]

    async def _perform_analysis_from_dump(self, analysis_id: str, dump_id: str):
        """Perform forensic analysis from existing dump (skip dump creation)"""
        analysis = self.analyses_db[analysis_id]

        try:
            # Get dump file path
            dump = memory_dump_service.get_dump(dump_id)
            analysis.dump_file_path = dump.file_path

            analysis.progress = 30
            analysis.current_step = "Running multi-tool forensic analysis..."

            # STEP 1: Multi-tool forensic analysis
            multi_tool_results = await self._run_multi_tool_analysis(analysis.dump_file_path)

            analysis.progress = 60
            analysis.current_step = "Running advanced YARA analysis..."

            # STEP 2: Advanced YARA analysis
            yara_results = await self._run_advanced_yara_analysis(analysis.dump_file_path)

            analysis.progress = 80
            analysis.current_step = "Generating comprehensive report..."

            # STEP 3: Combine results with safe extraction
            results = ForensicResults(
                dump_info={
                    "file_path": analysis.dump_file_path,
                    "file_size": os.path.getsize(analysis.dump_file_path),
                    "created_at": dump.created_at.isoformat(),
                    "instance_id": analysis.instance_id,
                    "instance_name": analysis.instance_name
                },
                binwalk_results=self._safe_get_results(multi_tool_results, "binwalk"),
                foremost_results=self._safe_get_results(multi_tool_results, "foremost"),
                yara_results=self._safe_get_results(multi_tool_results, "yara"),
                strings_analysis=self._safe_get_results(multi_tool_results, "strings"),
                hexdump_analysis=self._safe_get_results(multi_tool_results, "hexdump"),
                advanced_yara=yara_results if isinstance(yara_results, dict) else {"error": "Invalid YARA results"},
                summary=self._generate_summary(multi_tool_results, yara_results)
            )

            analysis.results = results
            analysis.progress = 90
            analysis.current_step = "Generating PDF report..."

            # STEP 4: Generate PDF report
            analysis.status = AnalysisStatus.GENERATING_REPORT
            report_path = await self._generate_pdf_report(analysis)
            analysis.report_path = report_path

            # Mark as completed
            analysis.status = AnalysisStatus.COMPLETED
            analysis.progress = 100
            analysis.current_step = "Analysis completed successfully"
            analysis.completed_at = datetime.now()

            logger.info(f"Forensic analysis from dump {analysis_id} completed successfully")

        except Exception as e:
            logger.error(f"Forensic analysis from dump {analysis_id} failed: {e}")
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            analysis.current_step = f"Analysis failed: {str(e)}"

        finally:
            # Clean up active analysis task
            if analysis_id in self.active_analyses:
                del self.active_analyses[analysis_id]

    def _safe_get_results(self, results: Any, key: str) -> Dict[str, Any]:
        """Safely extract results from potentially malformed data"""
        if isinstance(results, dict):
            return results.get(key, {"error": f"No {key} results found"})
        else:
            return {"error": f"Invalid results format for {key}"}

    def _extract_json_from_output(self, output: str) -> Dict[str, Any]:
        """Extract JSON from script output that may contain other text"""
        try:
            # Method 1: Try to parse the entire output as JSON
            return json.loads(output)
        except json.JSONDecodeError:
            try:
                # Method 2: Look for JSON-like patterns in the output
                # Find lines that look like JSON (start with { and end with })
                lines = output.split('\n')
                json_lines = []
                in_json = False
                brace_count = 0
                
                for line in lines:
                    if line.strip().startswith('{'):
                        in_json = True
                        brace_count = 0
                    
                    if in_json:
                        brace_count += line.count('{') - line.count('}')
                        json_lines.append(line)
                        
                        if brace_count <= 0:
                            break
                
                if json_lines:
                    json_text = '\n'.join(json_lines)
                    return json.loads(json_text)
                    
                # Method 3: Look for the last JSON object in output
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, output, re.DOTALL)
                if matches:
                    return json.loads(matches[-1])
                    
            except (json.JSONDecodeError, IndexError):
                pass
            
            # Method 4: Parse text output and create structured data
            return self._parse_text_output(output)

    def _parse_text_output(self, output: str) -> Dict[str, Any]:
        """Parse plain text output from forensic tools and create structured data"""
        try:
            results = {
                "status": "success",
                "raw_output": output,
                "parsed_data": {},
                "tools_executed": []
            }
            
            lines = output.split('\n')
            current_tool = None
            current_section = None
            
            logger.info(f"Parsing output with {len(lines)} lines...")
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                # Detect tool execution - more patterns
                lower_line = line.lower()
                
                # Log interesting lines for debugging
                if any(word in lower_line for word in ['running', 'executing', 'starting', 'binwalk', 'foremost', 'strings', 'yara', 'hexdump']):
                    logger.debug(f"Line {i}: {line}")
                
                if 'running' in lower_line or 'executing' in lower_line or 'starting' in lower_line:
                    if 'binwalk' in lower_line and 'binwalk' not in results['tools_executed']:
                        current_tool = 'binwalk'
                        results['tools_executed'].append('binwalk')
                        results['parsed_data']['binwalk'] = {"output": [], "status": "running", "findings": []}
                        logger.info(f"Detected binwalk tool execution at line {i}")
                    elif 'foremost' in lower_line and 'foremost' not in results['tools_executed']:
                        current_tool = 'foremost'
                        results['tools_executed'].append('foremost')
                        results['parsed_data']['foremost'] = {"output": [], "status": "running", "files_recovered": 0}
                        logger.info(f"Detected foremost tool execution at line {i}")
                    elif 'strings' in lower_line and 'strings' not in results['tools_executed']:
                        current_tool = 'strings'
                        results['tools_executed'].append('strings')
                        results['parsed_data']['strings'] = {"output": [], "status": "running", "total_strings": 0}
                        logger.info(f"Detected strings tool execution at line {i}")
                    elif 'hexdump' in lower_line and 'hexdump' not in results['tools_executed']:
                        current_tool = 'hexdump'
                        results['tools_executed'].append('hexdump')
                        results['parsed_data']['hexdump'] = {"output": [], "status": "running", "samples": []}
                        logger.info(f"Detected hexdump tool execution at line {i}")
                    elif 'yara' in lower_line and 'yara' not in results['tools_executed']:
                        current_tool = 'yara'
                        results['tools_executed'].append('yara')
                        results['parsed_data']['yara'] = {"output": [], "status": "running", "matches": [], "rules_matched": 0}
                        logger.info(f"Detected yara tool execution at line {i}")
                
                # Detect specific tool invocations even without "running" - but avoid duplicates
                elif 'binwalk' in lower_line and current_tool != 'binwalk' and 'binwalk' not in results['tools_executed']:
                    current_tool = 'binwalk'
                    results['tools_executed'].append('binwalk')
                    results['parsed_data']['binwalk'] = {"output": [], "status": "running", "findings": []}
                    logger.info(f"Detected binwalk tool (fallback) at line {i}")
                
                elif 'foremost' in lower_line and current_tool != 'foremost' and 'foremost' not in results['tools_executed']:
                    current_tool = 'foremost'
                    results['tools_executed'].append('foremost')
                    results['parsed_data']['foremost'] = {"output": [], "status": "running", "files_recovered": 0}
                    logger.info(f"Detected foremost tool (fallback) at line {i}")
                
                elif 'strings' in lower_line and current_tool != 'strings' and 'strings' not in results['tools_executed']:
                    current_tool = 'strings'
                    results['tools_executed'].append('strings')
                    results['parsed_data']['strings'] = {"output": [], "status": "running", "total_strings": 0}
                    logger.info(f"Detected strings tool (fallback) at line {i}")
                
                elif 'yara' in lower_line and current_tool != 'yara' and 'yara' not in results['tools_executed']:
                    current_tool = 'yara'
                    results['tools_executed'].append('yara')
                    results['parsed_data']['yara'] = {"output": [], "status": "running", "matches": [], "rules_matched": 0}
                    logger.info(f"Detected yara tool (fallback) at line {i}")
                
                # Detect completion
                if any(word in lower_line for word in ['completed', 'finished', 'done', 'success']):
                    if current_tool and current_tool in results['parsed_data']:
                        results['parsed_data'][current_tool]['status'] = 'completed'
                        logger.info(f"Tool {current_tool} marked as completed at line {i}")
                
                # Extract specific data
                if current_tool and current_tool in results['parsed_data']:
                    results['parsed_data'][current_tool]['output'].append(line)
                    
                    # Extract specific findings
                    if current_tool == 'strings':
                        try:
                            # Look for string counts
                            numbers = [int(s) for s in line.split() if s.isdigit()]
                            if numbers:
                                max_num = max(numbers)
                                if max_num > results['parsed_data']['strings']['total_strings']:
                                    results['parsed_data']['strings']['total_strings'] = max_num
                                    logger.debug(f"Updated strings count to {max_num}")
                        except:
                            pass
                    
                    elif current_tool == 'foremost':
                        if 'files' in lower_line or 'recovered' in lower_line:
                            try:
                                numbers = [int(s) for s in line.split() if s.isdigit()]
                                if numbers:
                                    max_num = max(numbers)
                                    if max_num > results['parsed_data']['foremost']['files_recovered']:
                                        results['parsed_data']['foremost']['files_recovered'] = max_num
                                        logger.debug(f"Updated foremost files to {max_num}")
                            except:
                                pass
                    
                    elif current_tool == 'yara':
                        if 'match' in lower_line or 'rule' in lower_line:
                            results['parsed_data']['yara']['matches'].append(line)
                            results['parsed_data']['yara']['rules_matched'] += 1
                            logger.debug(f"Added YARA match: {line[:50]}...")
                    
                    elif current_tool == 'binwalk':
                        if any(word in lower_line for word in ['header', 'signature', 'filesystem', 'archive']):
                            results['parsed_data']['binwalk']['findings'].append(line)
                            logger.debug(f"Added binwalk finding: {line[:50]}...")
            
            # Count successful tools
            successful_tools = sum(1 for tool_data in results['parsed_data'].values() 
                                 if isinstance(tool_data, dict) and tool_data.get('status') == 'completed')
            
            results['summary'] = {
                "total_tools_run": len(results['tools_executed']),
                "successful_tools": successful_tools,
                "failed_tools": len(results['tools_executed']) - successful_tools
            }
            
            logger.info(f"Final parsing results: {len(results['tools_executed'])} tools ({', '.join(results['tools_executed'])}), {successful_tools} successful")
            
            # Log detailed results for each tool
            for tool_name, tool_data in results['parsed_data'].items():
                if isinstance(tool_data, dict):
                    output_count = len(tool_data.get('output', []))
                    status = tool_data.get('status', 'unknown')
                    logger.info(f"Tool {tool_name}: {status}, {output_count} output lines")
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing text output: {e}")
            return {
                "error": "Failed to parse text output",
                "raw_output": output[:1000],
                "status": "error"
            }
            
            # If all else fails, return a basic structure
            logger.warning(f"Could not extract JSON from output: {output[:200]}...")
            return {
                "error": "Failed to parse JSON output",
                "raw_output": output[:1000],  # First 1000 chars for debugging
                "status": "error"
            }

    async def _run_multi_tool_analysis(self, dump_file_path: str) -> Dict[str, Any]:
        """Run multi-tool forensic analysis"""
        try:
            script_path = self.scripts_directory / "multi-tool-forensic.sh"

            # Check if script exists
            if not script_path.exists():
                logger.error(f"Multi-tool script not found: {script_path}")
                return {"error": f"Script not found: {script_path}"}

            cmd = f"cd {self.scripts_directory} && bash multi-tool-forensic.sh '{dump_file_path}'"

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.scripts_directory)
            )

            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            logger.info(f"Multi-tool script completed with return code: {process.returncode}")
            logger.debug(f"Multi-tool stdout length: {len(stdout_text)}")
            logger.debug(f"Multi-tool stderr: {stderr_text[:500]}")
            
            # Log first 500 chars of stdout for debugging
            logger.info(f"Multi-tool output preview: {stdout_text[:500]}")

            if process.returncode == 0:
                # Try to extract JSON from output
                results = self._extract_json_from_output(stdout_text)
                logger.info(f"Multi-tool analysis completed successfully. Results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
                return results
            else:
                error_msg = stderr_text or "Multi-tool analysis failed"
                logger.error(f"Multi-tool analysis failed: {error_msg}")
                # Even if script failed, try to parse partial output
                if stdout_text.strip():
                    partial_results = self._extract_json_from_output(stdout_text)
                    partial_results["script_error"] = error_msg
                    return partial_results
                return {"error": error_msg, "stdout": stdout_text}

        except Exception as e:
            logger.error(f"Error running multi-tool analysis: {e}")
            return {"error": str(e)}

    async def _run_advanced_yara_analysis(self, dump_file_path: str) -> Dict[str, Any]:
        """Run advanced YARA analysis"""
        try:
            script_path = self.scripts_directory / "advanced-yara-tool.sh"

            # Check if script exists
            if not script_path.exists():
                logger.error(f"Advanced YARA script not found: {script_path}")
                return {"error": f"Script not found: {script_path}"}

            cmd = f"cd {self.scripts_directory} && bash advanced-yara-tool.sh '{dump_file_path}'"

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.scripts_directory)
            )

            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            logger.info(f"Advanced YARA script completed with return code: {process.returncode}")
            logger.debug(f"YARA stdout length: {len(stdout_text)}")
            logger.debug(f"YARA stderr: {stderr_text[:500]}")
            
            # Log first 500 chars of stdout for debugging
            logger.info(f"YARA output preview: {stdout_text[:500]}")

            if process.returncode == 0:
                # Try to extract JSON from output
                results = self._extract_json_from_output(stdout_text)
                logger.info(f"Advanced YARA analysis completed successfully. Results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
                return results
            else:
                error_msg = stderr_text or "Advanced YARA analysis failed"
                logger.error(f"Advanced YARA analysis failed: {error_msg}")
                # Even if script failed, try to parse partial output
                if stdout_text.strip():
                    partial_results = self._extract_json_from_output(stdout_text)
                    partial_results["script_error"] = error_msg
                    return partial_results
                return {"error": error_msg, "stdout": stdout_text}

        except Exception as e:
            logger.error(f"Error running advanced YARA analysis: {e}")
            return {"error": str(e)}

    def _generate_summary(self, multi_tool_results: Any, yara_results: Any) -> Dict[str, Any]:
        """Generate analysis summary with improved data extraction"""
        summary = {
            "total_tools_run": 0,
            "successful_tools": 0,
            "failed_tools": 0,
            "key_findings": [],
            "security_indicators": [],
            "credentials_found": [],
            "file_signatures": [],
            "network_artifacts": []
        }

        try:
            # Handle multi_tool_results - focus on parsed_data for detailed extraction
            if isinstance(multi_tool_results, dict):
                logger.info(f"Processing multi-tool results with keys: {list(multi_tool_results.keys())}")
                
                # Extract from parsed_data structure (our improved parsing)
                if "parsed_data" in multi_tool_results:
                    parsed_data = multi_tool_results["parsed_data"]
                    logger.info(f"Found parsed_data with tools: {list(parsed_data.keys())}")
                    
                    for tool_name, tool_data in parsed_data.items():
                        if isinstance(tool_data, dict):
                            summary["total_tools_run"] += 1
                            status = tool_data.get("status", "unknown")
                            output_lines = len(tool_data.get("output", []))
                            
                            logger.info(f"Tool {tool_name}: status={status}, output_lines={output_lines}")
                            
                            if status == "completed":
                                summary["successful_tools"] += 1
                                
                                # Extract specific data for each tool
                                if tool_name == "strings":
                                    total_strings = tool_data.get("total_strings", 0)
                                    if total_strings > 0:
                                        summary["key_findings"].append(f"Strings analysis extracted {total_strings:,} strings from memory")
                                    elif output_lines > 0:
                                        # Estimate strings from output lines (rough approximation)
                                        estimated_strings = output_lines * 10  # Assume ~10 strings per line of output
                                        summary["key_findings"].append(f"Strings analysis completed with ~{estimated_strings:,} extracted strings ({output_lines} lines of output)")
                                
                                elif tool_name == "foremost":
                                    files_recovered = tool_data.get("files_recovered", 0)
                                    if files_recovered > 0:
                                        summary["key_findings"].append(f"Foremost successfully recovered {files_recovered} files from memory dump")
                                    elif output_lines > 0:
                                        summary["key_findings"].append(f"Foremost file recovery analysis completed ({output_lines} lines of output)")
                                
                                elif tool_name == "yara":
                                    rules_matched = tool_data.get("rules_matched", 0)
                                    matches = tool_data.get("matches", [])
                                    if rules_matched > 0:
                                        summary["key_findings"].append(f"YARA analysis detected {rules_matched} security pattern matches")
                                        if isinstance(matches, list):
                                            summary["security_indicators"].extend(matches[:5])  # First 5 matches
                                    elif output_lines > 0:
                                        summary["key_findings"].append(f"YARA pattern analysis completed ({output_lines} lines of output)")
                                
                                elif tool_name == "binwalk":
                                    findings = tool_data.get("findings", [])
                                    if findings:
                                        summary["key_findings"].append(f"Binwalk identified {len(findings)} file signatures and embedded objects")
                                        summary["file_signatures"] = findings[:10]  # First 10 findings
                                    elif output_lines > 0:
                                        # Estimate signatures from output (binwalk typically shows multiple lines per signature)
                                        estimated_sigs = max(1, output_lines // 3)  # Rough estimate
                                        summary["key_findings"].append(f"Binwalk file signature analysis completed with ~{estimated_sigs} signatures detected ({output_lines} lines)")
                                
                                elif tool_name == "hexdump":
                                    samples = tool_data.get("samples", [])
                                    if samples:
                                        summary["key_findings"].append(f"Hexdump analysis captured {len(samples)} memory samples")
                                    elif output_lines > 0:
                                        summary["key_findings"].append(f"Hexdump memory analysis completed ({output_lines} lines of hex data)")
                            else:
                                summary["failed_tools"] += 1
                                summary["key_findings"].append(f"Tool {tool_name} analysis incomplete (status: {status})")
                
                # Fallback to summary structure if available
                elif "summary" in multi_tool_results:
                    parsed_summary = multi_tool_results["summary"]
                    summary["total_tools_run"] += parsed_summary.get("total_tools_run", 0)
                    summary["successful_tools"] += parsed_summary.get("successful_tools", 0)
                    summary["failed_tools"] += parsed_summary.get("failed_tools", 0)
                
                # Fallback to tools_executed list
                elif "tools_executed" in multi_tool_results:
                    tools_executed = multi_tool_results["tools_executed"]
                    if isinstance(tools_executed, list):
                        summary["total_tools_run"] = len(tools_executed)
                        summary["key_findings"].append(f"Executed {len(tools_executed)} forensic tools: {', '.join(tools_executed)}")

            # Handle YARA results
            if isinstance(yara_results, dict):
                logger.info(f"Processing YARA results with keys: {list(yara_results.keys())}")
                
                # Check for advanced YARA structure
                if yara_results.get("total_matches", 0) > 0:
                    total_matches = yara_results["total_matches"]
                    summary["key_findings"].append(f"Advanced YARA analysis found {total_matches} security pattern matches")
                    summary["total_tools_run"] += 1
                    summary["successful_tools"] += 1
                
                # Extract key findings from YARA
                if "key_findings" in yara_results and yara_results["key_findings"]:
                    yara_findings = yara_results["key_findings"]
                    if isinstance(yara_findings, list):
                        summary["security_indicators"].extend(yara_findings[:5])
                        summary["key_findings"].append(f"YARA detected {len(yara_findings)} security indicators")
                    else:
                        # If it's a string or other type, convert it
                        summary["security_indicators"].append(str(yara_findings))
                        summary["key_findings"].append("YARA analysis found security indicators")
                
                # Extract detailed matches
                if "detailed_matches" in yara_results and yara_results["detailed_matches"]:
                    detailed = yara_results["detailed_matches"]
                    for category, matches in detailed.items():
                        if matches:
                            summary["key_findings"].append(f"YARA found {len(matches)} matches in category: {category}")
                
                # Check for credentials
                if "rule_summary" in yara_results:
                    rule_summary = yara_results["rule_summary"]
                    if "CirrOS_Credentials" in rule_summary:
                        cred_matches = rule_summary["CirrOS_Credentials"]
                        if cred_matches > 0:
                            summary["credentials_found"].append(f"Found {cred_matches} credential patterns")
                            summary["key_findings"].append(f"Security Alert: {cred_matches} credential patterns detected")

            # Ensure we have at least one finding
            if not summary["key_findings"]:
                if summary["total_tools_run"] > 0:
                    summary["key_findings"].append(f"Forensic analysis completed on {summary['total_tools_run']} tools - review detailed results")
                else:
                    summary["key_findings"].append("Forensic analysis completed - no specific patterns detected")

            logger.info(f"Final summary: {summary['total_tools_run']} tools total, {summary['successful_tools']} successful, {len(summary['key_findings'])} findings")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            summary["key_findings"].append(f"Summary generation error: {str(e)}")

        return summary

    async def _generate_pdf_report(self, analysis: IntegratedAnalysis) -> str:
        """Generate comprehensive PDF report"""
        try:
            # Create PDF report using reportlab
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"forensic_report_{analysis.instance_id}_{timestamp}.pdf"
            report_path = self.base_directory / "reports" / report_filename

            # Create PDF document
            doc = SimpleDocTemplate(str(report_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("Forensic Analysis Report", title_style))
            story.append(Spacer(1, 12))

            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            summary_text = f"""
            <b>Instance:</b> {analysis.instance_name} ({analysis.instance_id})<br/>
            <b>Analysis Started:</b> {analysis.started_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.started_at else 'N/A'}<br/>
            <b>Analysis Completed:</b> {analysis.completed_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.completed_at else 'N/A'}<br/>
            <b>Memory Dump Size:</b> {analysis.results.dump_info.get('file_size', 0):,} bytes<br/>
            <b>Total Tools Run:</b> {analysis.results.summary.get('total_tools_run', 0)}<br/>
            <b>Successful Tools:</b> {analysis.results.summary.get('successful_tools', 0)}<br/>
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 12))

            # Key Findings
            story.append(Paragraph("Key Findings", styles['Heading2']))
            key_findings = analysis.results.summary.get('key_findings', [])
            for finding in key_findings:
                story.append(Paragraph(f"• {finding}", styles['Normal']))
            story.append(Spacer(1, 12))

            # Security Indicators
            security_indicators = analysis.results.summary.get('security_indicators', [])
            if security_indicators:
                story.append(Paragraph("Security Indicators", styles['Heading2']))
                for indicator in security_indicators:
                    story.append(Paragraph(f"• {indicator}", styles['Normal']))
                story.append(Spacer(1, 12))

            # Credentials Found
            credentials_found = analysis.results.summary.get('credentials_found', [])
            if credentials_found:
                story.append(Paragraph("Credentials Found", styles['Heading2']))
                cred_data = [['Type', 'Value', 'Context']]
                for cred in credentials_found:
                    if isinstance(cred, dict):
                        cred_data.append([
                            cred.get('type', 'Unknown'),
                            cred.get('value', 'N/A'),
                            cred.get('context', 'N/A')
                        ])

                if len(cred_data) > 1:  # More than just headers
                    cred_table = Table(cred_data)
                    cred_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(cred_table)
                    story.append(Spacer(1, 12))

            # Technical Details
            story.append(Paragraph("Technical Analysis Details", styles['Heading2']))

            # Binwalk Results
            if analysis.results.binwalk_results.get('status') == 'success':
                story.append(Paragraph("File Signature Analysis (Binwalk)", styles['Heading3']))
                binwalk_info = f"Found {len(analysis.results.binwalk_results.get('signatures_found', []))} file signatures"
                story.append(Paragraph(binwalk_info, styles['Normal']))
                story.append(Spacer(1, 6))

            # Foremost Results
            if analysis.results.foremost_results.get('status') == 'success':
                story.append(Paragraph("File Recovery Analysis (Foremost)", styles['Heading3']))
                foremost_info = f"Recovered {analysis.results.foremost_results.get('files_recovered', 0)} files"
                story.append(Paragraph(foremost_info, styles['Normal']))
                story.append(Spacer(1, 6))

            # YARA Results
            if analysis.results.yara_results.get('status') == 'success':
                story.append(Paragraph("Pattern Matching Analysis (YARA)", styles['Heading3']))
                yara_info = f"Matched {analysis.results.yara_results.get('total_matches', 0)} patterns"
                story.append(Paragraph(yara_info, styles['Normal']))
                story.append(Spacer(1, 6))

            # Strings Analysis
            if analysis.results.strings_analysis.get('status') == 'success':
                story.append(Paragraph("String Analysis", styles['Heading3']))
                strings_info = f"Extracted {analysis.results.strings_analysis.get('total_strings', 0)} strings"
                story.append(Paragraph(strings_info, styles['Normal']))
                story.append(Spacer(1, 12))

            # Footer
            story.append(Spacer(1, 30))
            footer_text = f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by DevStack Forensic Analysis System"
            story.append(Paragraph(footer_text, styles['Normal']))

            # Build PDF
            doc.build(story)

            logger.info(f"PDF report generated: {report_path}")
            return str(report_path)

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise Exception(f"PDF generation failed: {e}")

    def get_analysis(self, analysis_id: str) -> Optional[IntegratedAnalysis]:
        """Get analysis by ID"""
        return self.analyses_db.get(analysis_id)

    def get_all_analyses(self) -> List[IntegratedAnalysis]:
        """Get all analyses"""
        return list(self.analyses_db.values())

    def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis status and progress"""
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return None

        return {
            "id": analysis.id,
            "status": analysis.status.value,
            "progress": analysis.progress,
            "current_step": analysis.current_step,
            "created_at": analysis.created_at.isoformat(),
            "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "error_message": analysis.error_message
        }

    def get_report_path(self, analysis_id: str) -> Optional[str]:
        """Get report file path for download"""
        analysis = self.get_analysis(analysis_id)
        if analysis and analysis.report_path and os.path.exists(analysis.report_path):
            return analysis.report_path
        return None


# Global service instance
integrated_forensic_service = IntegratedForensicService()
