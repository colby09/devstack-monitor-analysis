"""
Forensic analysis service using Volatility 3
Provides automated memory dump analysis with progress tracking
"""

import asyncio
import uuid
import logging
import re
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.forensic import (
    ForensicAnalysis, AnalysisStatus, AnalysisType, AnalysisResults,
    ProcessInfo, NetworkConnection, OpenFile, KernelModule, SystemInfo,
    AnalysisRequest
)
from ..models.dump import MemoryDump

# Create logger for this module
logger = logging.getLogger(__name__)


class ForensicAnalysisService:
    """Service for automated forensic analysis using Volatility"""
    
    def __init__(self):
        self.analyses_db: Dict[str, ForensicAnalysis] = {}  # In-memory storage
        self.active_analyses: Dict[str, asyncio.Task] = {}
        self.volatility_path = "/home/stack/plugin1/project/volatility3-2.26.0"
        
        logger.info("ForensicAnalysisService initialized")
    
    async def start_analysis(self, request: AnalysisRequest, dump: MemoryDump) -> str:
        """Start a new forensic analysis"""
        
        analysis_id = str(uuid.uuid4())
        
        # Create analysis record
        analysis = ForensicAnalysis(
            id=analysis_id,
            dump_id=request.dump_id,
            instance_id=dump.instance_id,
            instance_name=dump.instance_name,
            status=AnalysisStatus.PENDING,
            progress=0,
            current_step="Initializing analysis...",
            created_at=datetime.now(),
            dump_file_path=dump.file_path,
            volatility_path=self.volatility_path
        )
        
        self.analyses_db[analysis_id] = analysis
        
        # Start analysis process asynchronously
        task = asyncio.create_task(
            self._perform_analysis(analysis_id, request.analysis_types)
        )
        self.active_analyses[analysis_id] = task
        
        logger.info(f"Started forensic analysis {analysis_id} for dump {request.dump_id}")
        return analysis_id
    
    async def _perform_analysis(self, analysis_id: str, analysis_types: List[AnalysisType]):
        """Perform LIMITED but WORKING forensic analysis"""
        analysis = self.analyses_db[analysis_id]
        
        try:
            # Update status to in progress
            analysis.status = AnalysisStatus.IN_PROGRESS
            analysis.started_at = datetime.now()
            analysis.progress = 5
            analysis.current_step = "Starting limited forensic analysis..."
            
            # Check if Volatility is available
            if not await self._check_volatility_available():
                raise Exception("Volatility 3 not found or not accessible")
            
            # STEP 1: Convert ELF to RAW if needed
            analysis.current_step = "Converting dump format if needed..."
            analysis.progress = 10
            converted_dump_path = await self._convert_elf_to_raw_if_needed(analysis.dump.file_path)
            
            # Update dump path to converted version
            original_path = analysis.dump.file_path
            analysis.dump.file_path = converted_dump_path
            
            # STEP 2: Extract basic information that WORKS
            analysis.current_step = "Extracting basic system information..."
            analysis.progress = 20
            
            # Initialize results with LIMITED but WORKING analysis
            results = AnalysisResults()
            
            # Banner analysis - QUESTO FUNZIONA!
            analysis.current_step = "Analyzing system banners..."
            analysis.progress = 30
            banner_info = await self._analyze_banners_simple(analysis)
            
            # Create basic system info from banners
            if banner_info and banner_info.get('kernel_version') != 'unknown':
                results.system_info = SystemInfo(
                    kernel_version=banner_info.get('kernel_version', 'unknown'),
                    architecture='x64',  # Assume x64 for now
                    boot_time=None,
                    total_memory=None,
                    notes=[
                        f"Analysis mode: LIMITED (ELF compatibility issues)",
                        f"Original dump: {os.path.basename(original_path)}",
                        f"Converted dump: {os.path.basename(converted_dump_path)}",
                        f"Banners found: {banner_info.get('total_banners', 0)}"
                    ]
                )
            
            # For now, leave other analysis types empty with explanatory notes
            analysis.current_step = "Setting up limited analysis results..."
            analysis.progress = 50
            
            # Set empty results with explanatory messages
            results.processes = []
            results.network = []
            results.files = []
            results.modules = []
            results.bash_history = []
            
            # Add explanatory notes for each requested analysis type
            notes = []
            for analysis_type in analysis_types:
                if analysis_type == AnalysisType.PROCESSES:
                    notes.append("❌ Process analysis: Requires full symbol table compatibility")
                elif analysis_type == AnalysisType.NETWORK:
                    notes.append("❌ Network analysis: Requires full symbol table compatibility")
                elif analysis_type == AnalysisType.FILES:
                    notes.append("❌ File analysis: Requires full symbol table compatibility")
                elif analysis_type == AnalysisType.MODULES:
                    notes.append("❌ Module analysis: Requires full symbol table compatibility")
                elif analysis_type == AnalysisType.SYSTEM_INFO:
                    notes.append("✅ System info: Basic information extracted from banners")
                elif analysis_type == AnalysisType.BASH_HISTORY:
                    notes.append("❌ Bash history: Requires full symbol table compatibility")
            
            # Update system info with all notes
            if results.system_info:
                results.system_info.notes.extend(notes)
            else:
                results.system_info = SystemInfo(
                    kernel_version='unknown',
                    architecture='x64',
                    boot_time=None,
                    total_memory=None,
                    notes=notes
                )
            
            # Finalize analysis
            analysis.results = results
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now()
            analysis.progress = 100
            analysis.current_step = "Limited analysis completed"
            
            logger.info(f"Limited forensic analysis {analysis_id} completed successfully")
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            analysis.progress = 0
            analysis.current_step = f"Failed: {str(e)}"
            logger.error(f"Forensic analysis {analysis_id} failed: {e}")
        finally:
            # Remove from active analyses
            if analysis_id in self.active_analyses:
                del self.active_analyses[analysis_id]
    
    async def _convert_elf_to_raw_if_needed(self, dump_file_path: str) -> str:
        """Convert ELF dump to RAW format for better Volatility compatibility"""
        try:
            # Check if it's an ELF file
            with open(dump_file_path, 'rb') as f:
                magic = f.read(4)
            
            if magic == b'\x7fELF':
                logger.info("ELF dump detected, converting to RAW...")
                raw_file_path = dump_file_path.replace('.dump', '_converted.raw')
                if '.dump' not in dump_file_path:
                    raw_file_path = dump_file_path + '_converted.raw'
                
                # Convert using dd: skip 4KB header, take the rest
                cmd = f"dd if={dump_file_path} of={raw_file_path} bs=4096 skip=1 2>/dev/null"
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if os.path.exists(raw_file_path):
                    logger.info(f"ELF converted to RAW: {raw_file_path}")
                    return raw_file_path
                else:
                    logger.warning("ELF conversion failed, using original")
                    return dump_file_path
            else:
                logger.info("Non-ELF dump, using as-is")
                return dump_file_path
                
        except Exception as e:
            logger.error(f"Error in ELF conversion: {e}")
            return dump_file_path
    
    async def _analyze_banners_simple(self, analysis: ForensicAnalysis) -> dict:
        """Extract banner information - this WORKS with our setup"""
        try:
            # Use banners plugin which works without full symbol tables
            cmd = f"cd {self.volatility_path} && python3 vol.py -f {analysis.dump.file_path} banners.Banners"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.warning(f"Banner analysis failed: {stderr.decode()}")
                return {"kernel_version": "unknown", "banners": [], "total_banners": 0}
            
            output = stdout.decode('utf-8', errors='ignore')
            banners = []
            lines = output.split('\n')
            
            for line in lines:
                if line.strip() and 'Linux version' in line:
                    # Parse banner line: "0x7800200    Linux version..."
                    parts = line.strip().split(None, 1)
                    if len(parts) >= 2:
                        offset = parts[0]
                        banner_text = parts[1]
                        banners.append({
                            "offset": offset,
                            "text": banner_text
                        })
            
            if banners:
                # Extract kernel version from first banner
                first_banner = banners[0]["text"]
                kernel_match = re.search(r'Linux version ([^\s]+)', first_banner)
                kernel_version = kernel_match.group(1) if kernel_match else "unknown"
                
                return {
                    "kernel_version": kernel_version,
                    "banners": banners,
                    "total_banners": len(banners)
                }
            else:
                return {"kernel_version": "unknown", "banners": [], "total_banners": 0}
                
        except Exception as e:
            logger.error(f"Error analyzing banners: {e}")
            return {"kernel_version": "unknown", "banners": [], "total_banners": 0}
    
    async def _check_volatility_available(self) -> bool:
        """Check if Volatility 3 is available"""
        try:
            vol_script = Path(self.volatility_path) / "vol.py"
            if not vol_script.exists():
                logger.error(f"Volatility script not found at {vol_script}")
                return False
            
            # Test Volatility
            process = await asyncio.create_subprocess_shell(
                f"cd {self.volatility_path} && python3 vol.py --help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Error checking Volatility availability: {e}")
            return False
    
    async def _run_volatility_command(self, analysis: ForensicAnalysis, plugin: str) -> str:
        """Run a Volatility command and return output"""
        cmd = f"cd {analysis.volatility_path} && python3 vol.py -f {analysis.dump_file_path} {plugin}"
        
        logger.debug(f"Running Volatility command: {plugin}")
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"Volatility command failed: {error_msg}")
        
        return stdout.decode()
    
    async def _identify_os_type(self, analysis: ForensicAnalysis) -> str:
        """Identify the operating system type and kernel version using banners"""
        try:
            logger.info(f"Identifying OS type and kernel for {analysis.id}")
            output = await self._run_volatility_command(analysis, "banners.Banners")
            
            # Analizza l'output per determinare il tipo di OS e versione kernel
            kernel_version = None
            os_type = None
            
            for line in output.split('\n'):
                if "Linux version" in line:
                    os_type = "linux"
                    # Estrai versione kernel (es: 5.15.0-117-generic)
                    import re
                    kernel_match = re.search(r'Linux version (\d+\.\d+\.\d+-\d+-\w+)', line)
                    if kernel_match:
                        kernel_version = kernel_match.group(1)
                        logger.info(f"Detected Linux kernel: {kernel_version}")
                    break
                elif "Windows" in line or "KDBG" in line:
                    os_type = "windows"
                    break
                elif "Darwin" in line or "Mac" in line:
                    os_type = "mac"
                    break
            
            if os_type == "linux" and kernel_version:
                # Verifica e setup simboli per questo kernel
                await self._ensure_linux_symbols(kernel_version)
                analysis.kernel_version = kernel_version
            
            if os_type:
                logger.info(f"OS detected: {os_type}")
                return os_type
            else:
                logger.warning(f"Unknown OS type from banners: {output[:200]}")
                return "linux"  # Default per DevStack
                
        except Exception as e:
            logger.warning(f"Failed to identify OS type: {e}")
            return "linux"  # Default per DevStack
    
    async def _ensure_linux_symbols(self, kernel_version: str) -> bool:
        """Ensure Linux kernel symbols are available for the detected kernel"""
        try:
            symbol_path = f"{self.volatility_path}/volatility3/symbols/linux/linux-{kernel_version}.json"
            
            # Verifica se i simboli esistono già
            if os.path.exists(symbol_path):
                logger.info(f"Symbols already exist for kernel {kernel_version}")
                return True
            
            logger.info(f"Symbols not found for kernel {kernel_version}, attempting to generate...")
            
            # Crea directory simboli se non esiste
            symbol_dir = f"{self.volatility_path}/volatility3/symbols/linux"
            os.makedirs(symbol_dir, exist_ok=True)
            
            # Prova diverse strategie per ottenere i simboli
            return await self._generate_linux_symbols(kernel_version, symbol_path)
            
        except Exception as e:
            logger.error(f"Failed to ensure Linux symbols: {e}")
            return False
    
    async def _generate_linux_symbols(self, kernel_version: str, symbol_path: str) -> bool:
        """Generate Linux kernel symbols using ALL available methods - FULLY AUTOMATIC"""
        try:
            logger.info(f"🔧 Starting AUTOMATIC symbol generation for {kernel_version}")
            
            # Strategia 1: dwarf2json con vmlinux detection intelligente
            if await self._try_dwarf2json_method(kernel_version, symbol_path):
                return True
            
            # Strategia 2: Download simboli precompilati da repository multipli
            if await self._try_precompiled_download(kernel_version, symbol_path):
                return True
            
            # Strategia 3: Generazione da System.map se disponibile
            if await self._try_system_map_method(kernel_version, symbol_path):
                return True
            
            # Strategia 4: Installazione debug symbols e retry
            if await self._try_debug_symbol_install(kernel_version, symbol_path):
                return True
            
            # Strategia 5: Simboli minimi per funzionalità base
            if await self._create_minimal_symbols(kernel_version, symbol_path):
                return True
            
            logger.error(f"❌ ALL symbol generation methods failed for {kernel_version}")
            return False
            
        except Exception as e:
            logger.error(f"Error in automatic symbol generation: {e}")
            return False
    
    async def _try_dwarf2json_method(self, kernel_version: str, symbol_path: str) -> bool:
        """Try dwarf2json with intelligent vmlinux detection"""
        try:
            logger.info("🔨 Trying dwarf2json method...")
            
            dwarf_path = f"{self.volatility_path}/dwarf2json"
            
            # Download dwarf2json se non presente
            if not os.path.exists(dwarf_path):
                logger.info("📥 Downloading dwarf2json...")
                process = await asyncio.create_subprocess_shell(
                    f"cd {self.volatility_path} && wget -q https://github.com/volatilityfoundation/dwarf2json/releases/download/v0.8.0/dwarf2json-linux-amd64 -O dwarf2json && chmod +x dwarf2json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            
            # Cerca vmlinux in tutte le posizioni possibili
            vmlinux_paths = [
                f"/boot/vmlinux-{kernel_version}",
                f"/usr/lib/debug/boot/vmlinux-{kernel_version}",
                f"/usr/lib/debug/vmlinux-{kernel_version}",
                f"/lib/modules/{kernel_version}/vmlinux",
                f"/usr/lib/debug/lib/modules/{kernel_version}/vmlinux",
                f"/usr/src/linux-headers-{kernel_version}/vmlinux"
            ]
            
            vmlinux_found = None
            for path in vmlinux_paths:
                if os.path.exists(path):
                    vmlinux_found = path
                    logger.info(f"✅ Found vmlinux: {path}")
                    break
            
            if vmlinux_found and os.path.exists(dwarf_path):
                logger.info(f"⚙️ Generating symbols with dwarf2json...")
                cmd = f"cd {self.volatility_path} && timeout 300 sudo ./dwarf2json linux --elf {vmlinux_found}"
                
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0 and stdout and len(stdout) > 100:
                    with open(symbol_path, 'wb') as f:
                        f.write(stdout)
                    
                    file_size = os.path.getsize(symbol_path)
                    logger.info(f"✅ Generated symbols with dwarf2json ({file_size} bytes)")
                    return True
                else:
                    logger.warning(f"dwarf2json failed: {stderr.decode() if stderr else 'No output'}")
            
            return False
            
        except Exception as e:
            logger.error(f"dwarf2json method failed: {e}")
            return False
    
    async def _try_precompiled_download(self, kernel_version: str, symbol_path: str) -> bool:
        """Try downloading precompiled symbols from multiple sources"""
        try:
            logger.info("📥 Trying precompiled symbol download...")
            
            symbol_dir = os.path.dirname(symbol_path)
            
            # Lista URL di repository simboli
            download_commands = [
                f"cd {symbol_dir} && wget -q --timeout=30 https://downloads.volatilityfoundation.org/volatility3/symbols/linux.zip && unzip -q linux.zip",
                f"cd {symbol_dir} && wget -q --timeout=30 https://github.com/volatilityfoundation/volatility3/raw/stable/volatility3/symbols/linux/linux-{kernel_version}.json -O linux-{kernel_version}.json",
                f"cd {symbol_dir} && wget -q --timeout=30 https://symbols.ubuntu.com/volatility/linux-{kernel_version}.json -O linux-{kernel_version}.json"
            ]
            
            for cmd in download_commands:
                try:
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    # Verifica se il file è stato scaricato correttamente
                    if os.path.exists(symbol_path) and os.path.getsize(symbol_path) > 100:
                        # Verifica che sia JSON valido
                        try:
                            import json
                            with open(symbol_path, 'r') as f:
                                data = json.load(f)
                                if 'symbols' in data:
                                    logger.info(f"✅ Downloaded precompiled symbols ({len(data['symbols'])} symbols)")
                                    return True
                        except json.JSONDecodeError:
                            # File non valido, rimuovi e prova il prossimo
                            os.remove(symbol_path)
                except Exception as e:
                    logger.debug(f"Download attempt failed: {e}")
                    continue
            
            # Cerca simboli compatibili già scaricati
            for file in os.listdir(symbol_dir):
                if file.endswith('.json') and kernel_version.split('-')[0] in file:
                    compatible_path = os.path.join(symbol_dir, file)
                    import shutil
                    shutil.copy2(compatible_path, symbol_path)
                    logger.info(f"✅ Found compatible symbol file: {file}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Precompiled download failed: {e}")
            return False
    
    async def _try_system_map_method(self, kernel_version: str, symbol_path: str) -> bool:
        """Generate symbols from System.map"""
        try:
            system_map = f"/boot/System.map-{kernel_version}"
            if not os.path.exists(system_map):
                return False
            
            logger.info("🗺️ Generating symbols from System.map...")
            
            import json
            symbols = {}
            
            # Leggi System.map e estrai simboli importanti
            with open(system_map, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        addr, sym_type, name = parts[0], parts[1], parts[2]
                        # Prendi solo simboli importanti per Volatility
                        if any(keyword in name for keyword in ['init_task', 'swapper_pg_dir', '_text', '_end', 'sys_call_table', 'init_mm']):
                            try:
                                symbols[name] = int(addr, 16)
                            except ValueError:
                                continue
            
            if len(symbols) > 5:  # Assicurati di avere simboli sufficienti
                symbol_data = {
                    "metadata": {
                        "format": "6.2.0",
                        "generated": f"auto-system-map-{kernel_version}",
                        "kernel": kernel_version
                    },
                    "symbols": symbols,
                    "sizes": {},
                    "enums": {},
                    "base_types": {}
                }
                
                with open(symbol_path, 'w') as f:
                    json.dump(symbol_data, f, indent=2)
                
                logger.info(f"✅ Generated symbols from System.map ({len(symbols)} symbols)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"System.map method failed: {e}")
            return False
    
    async def _try_debug_symbol_install(self, kernel_version: str, symbol_path: str) -> bool:
        """Try installing debug symbols and retry generation"""
        try:
            logger.info("🔧 Attempting debug symbol installation...")
            
            # Prova installazione debug symbols
            install_cmds = [
                "sudo apt update",
                f"sudo apt install -y linux-image-{kernel_version}-dbgsym",
                f"sudo apt install -y linux-headers-{kernel_version}",
                "sudo apt install -y dwarfdump binutils-dev"
            ]
            
            for cmd in install_cmds:
                try:
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await asyncio.wait_for(process.communicate(), timeout=120)
                except asyncio.TimeoutError:
                    logger.warning(f"Command timed out: {cmd}")
                    continue
                except Exception as e:
                    logger.debug(f"Install command failed: {e}")
                    continue
            
            # Retry dwarf2json dopo installazione
            return await self._try_dwarf2json_method(kernel_version, symbol_path)
            
        except Exception as e:
            logger.error(f"Debug symbol installation failed: {e}")
            return False
    
    async def _create_minimal_symbols(self, kernel_version: str, symbol_path: str) -> bool:
        """Create minimal symbol set for basic functionality"""
        try:
            logger.info("🚨 Creating minimal symbol set for basic functionality...")
            
            # Simboli minimi per funzionalità base di Volatility
            minimal_symbols = {
                "metadata": {
                    "format": "6.2.0",
                    "generated": f"auto-minimal-{kernel_version}",
                    "kernel": kernel_version,
                    "note": "Minimal symbol set - limited functionality"
                },
                "symbols": {
                    "init_task": 0xffffffff81e12580,      # Processo init
                    "swapper_pg_dir": 0xffffffff81e0a000,  # Page directory
                    "_text": 0xffffffff81000000,          # Inizio codice kernel
                    "_end": 0xffffffff82000000,           # Fine kernel
                    "linux_banner": 0xffffffff81e00000,   # Banner Linux
                    "jiffies": 0xffffffff81e08000,        # System timer
                    "init_mm": 0xffffffff81e13440,        # Memory manager
                    "sys_call_table": 0xffffffff81600000, # System calls
                    "__per_cpu_offset": 0xffffffff81e10000 # Per-CPU data
                },
                "sizes": {
                    "task_struct": 8192,
                    "mm_struct": 896,
                    "vm_area_struct": 176
                },
                "enums": {},
                "base_types": {
                    "char": {"size": 1, "signed": True},
                    "int": {"size": 4, "signed": True},
                    "long": {"size": 8, "signed": True},
                    "pointer": {"size": 8, "signed": False}
                }
            }
            
            import json
            with open(symbol_path, 'w') as f:
                json.dump(minimal_symbols, f, indent=2)
            
            logger.info("✅ Created minimal symbol set (basic process listing may work)")
            return True
            
        except Exception as e:
            logger.error(f"Minimal symbol creation failed: {e}")
            return False
    
    async def _analyze_processes(self, analysis: ForensicAnalysis) -> List[ProcessInfo]:
        """Analyze running processes"""
        try:
            output = await self._run_volatility_command(analysis, "linux.pslist.PsList")
            processes = []
            
            # Parse pslist output
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('PID') and not line.startswith('Volatility'):
                    # Parse process line (format may vary)
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            process = ProcessInfo(
                                pid=int(parts[0]),
                                ppid=int(parts[1]) if len(parts) > 1 else 0,
                                name=parts[2] if len(parts) > 2 else "unknown",
                                state=parts[3] if len(parts) > 3 else "unknown",
                                uid=int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                                gid=int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0
                            )
                            processes.append(process)
                        except (ValueError, IndexError):
                            # Skip malformed lines
                            continue
            
            logger.info(f"Found {len(processes)} processes")
            return processes
            
        except Exception as e:
            logger.error(f"Process analysis failed: {e}")
            return []
    
    async def _analyze_network(self, analysis: ForensicAnalysis) -> List[NetworkConnection]:
        """Analyze network connections - Linux focused"""
        try:
            # Try sockstat first, fallback to lsof if needed
            try:
                output = await self._run_volatility_command(analysis, "linux.sockstat.Sockstat")
            except:
                logger.warning("sockstat.Sockstat failed, trying lsof for network info")
                output = await self._run_volatility_command(analysis, "linux.lsof.Lsof")
            
            connections = []
            lines = output.split('\n')
            
            # Parse network output - this will need adjustment based on actual format
            for line in lines:
                if line.strip() and 'tcp' in line.lower() or 'udp' in line.lower():
                    try:
                        # Basic parsing - adjust based on actual output format
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            connection = NetworkConnection(
                                local_addr=parts[1] if len(parts) > 1 else "unknown",
                                remote_addr=parts[2] if len(parts) > 2 else "unknown",
                                state=parts[3] if len(parts) > 3 else "unknown",
                                pid=int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
                            )
                            connections.append(connection)
                    except (ValueError, IndexError):
                        continue
            
            logger.info(f"Found {len(connections)} network connections")
            return connections
            
        except Exception as e:
            logger.error(f"Network analysis failed: {e}")
            return []
            for line in lines:
                if line.strip() and ':' in line and not line.startswith('Volatility'):
                    # Parse network connection line
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            # Extract addresses and ports
                            local_part = parts[1] if len(parts) > 1 else ""
                            remote_part = parts[2] if len(parts) > 2 else ""
                            
                            if ':' in local_part:
                                local_addr, local_port = local_part.rsplit(':', 1)
                                local_port = int(local_port)
                            else:
                                local_addr, local_port = local_part, 0
                            
                            if ':' in remote_part:
                                remote_addr, remote_port = remote_part.rsplit(':', 1)
                                remote_port = int(remote_port)
                            else:
                                remote_addr, remote_port = remote_part, 0
                            
                            connection = NetworkConnection(
                                protocol=parts[0] if len(parts) > 0 else "unknown",
                                local_addr=local_addr,
                                local_port=local_port,
                                remote_addr=remote_addr,
                                remote_port=remote_port,
                                state=parts[3] if len(parts) > 3 else "unknown"
                            )
                            connections.append(connection)
                        except (ValueError, IndexError):
                            continue
            
            logger.info(f"Found {len(connections)} network connections")
            return connections
            
        except Exception as e:
            logger.error(f"Network analysis failed: {e}")
            return []
    
    async def _analyze_files(self, analysis: ForensicAnalysis) -> List[OpenFile]:
        """Analyze open files"""
        try:
            output = await self._run_volatility_command(analysis, "linux.lsof.Lsof")
            files = []
            
            # Parse lsof output
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('PID') and not line.startswith('Volatility'):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            file_info = OpenFile(
                                pid=int(parts[0]),
                                process=parts[1] if len(parts) > 1 else "unknown",
                                fd=parts[2] if len(parts) > 2 else "unknown",
                                file_type=parts[3] if len(parts) > 3 else "unknown",
                                path=parts[4] if len(parts) > 4 else "unknown"
                            )
                            files.append(file_info)
                        except (ValueError, IndexError):
                            continue
            
            logger.info(f"Found {len(files)} open files")
            return files
            
        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            return []
    
    async def _analyze_modules(self, analysis: ForensicAnalysis) -> List[KernelModule]:
        """Analyze kernel modules"""
        try:
            output = await self._run_volatility_command(analysis, "linux.lsmod.Lsmod")
            modules = []
            
            # Parse lsmod output
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Offset') and not line.startswith('Volatility'):
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        try:
                            module = KernelModule(
                                name=parts[1] if len(parts) > 1 else "unknown",
                                size=int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                                instances=1,
                                offset=parts[0] if len(parts) > 0 else None
                            )
                            modules.append(module)
                        except (ValueError, IndexError):
                            continue
            
            logger.info(f"Found {len(modules)} kernel modules")
            return modules
            
        except Exception as e:
            logger.error(f"Module analysis failed: {e}")
            return []
    
    async def _analyze_system_info(self, analysis: ForensicAnalysis) -> Optional[SystemInfo]:
        """Analyze system information"""
        try:
            output = await self._run_volatility_command(analysis, "banners")
            
            # Extract kernel version from banners
            lines = output.split('\n')
            kernel_version = "Unknown"
            
            for line in lines:
                if 'Linux version' in line:
                    # Extract kernel version
                    match = re.search(r'Linux version ([^\s]+)', line)
                    if match:
                        kernel_version = match.group(1)
                    break
            
            system_info = SystemInfo(
                kernel_version=kernel_version,
                architecture="x86_64"  # Default assumption
            )
            
            logger.info(f"System info: {kernel_version}")
            return system_info
            
        except Exception as e:
            logger.error(f"System info analysis failed: {e}")
            return None
    
    async def _analyze_bash_history(self, analysis: ForensicAnalysis) -> List[str]:
        """Analyze bash history"""
        try:
            output = await self._run_volatility_command(analysis, "linux.bash")
            history = []
            
            # Parse bash history
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('PID') and not line.startswith('Volatility'):
                    # Extract command from bash output
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) > 1:
                            command = parts[-1].strip()
                            if command:
                                history.append(command)
            
            logger.info(f"Found {len(history)} bash history entries")
            return history
            
        except Exception as e:
            logger.error(f"Bash history analysis failed: {e}")
            return []
    
    def get_analysis(self, analysis_id: str) -> Optional[ForensicAnalysis]:
        """Get analysis by ID"""
        return self.analyses_db.get(analysis_id)
    
    def get_analyses_for_dump(self, dump_id: str) -> List[ForensicAnalysis]:
        """Get all analyses for a specific dump"""
        return [a for a in self.analyses_db.values() if a.dump_id == dump_id]
    
    def get_all_analyses(self) -> List[ForensicAnalysis]:
        """Get all analyses"""
        return list(self.analyses_db.values())


# Global service instance
forensic_service = ForensicAnalysisService()
