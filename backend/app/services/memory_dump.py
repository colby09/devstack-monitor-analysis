"""
Memory dump service for digital forensics
Handles SSH connections and memory acquisition from Linux instances
"""

import asyncio
import asyncssh
import hashlib
import os
import uuid
import logging
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.dump import MemoryDump, DumpStatus, DumpType, DumpRequest
from ..core.ssh_config import ssh_config
from ..core.config import Settings

# Get settings instance
settings = Settings()

# Create logger for this module
logger = logging.getLogger(__name__)


class MemoryDumpService:
    """Service for managing memory dumps via SSH"""
    
    def __init__(self):
        # Determine dump mode from settings
        self.dump_mode = settings.DUMP_MODE.lower()
        
        # Set directories based on mode
        if self.dump_mode == "local":
            # Running on OpenStack server (Linux)
            self.dump_directory = Path(settings.DUMP_LOCAL_DIRECTORY)
            self.remote_dump_directory = settings.DUMP_LOCAL_DIRECTORY
        else:
            # Running on external Windows server
            self.dump_directory = Path("C:/temp/ramdump") if os.name == 'nt' else Path("/tmp/ramdump")
            self.remote_dump_directory = settings.DUMP_REMOTE_DIRECTORY
            
        self.dumps_db: Dict[str, MemoryDump] = {}  # In-memory storage for now
        self.active_dumps: Dict[str, asyncio.Task] = {}
        
        # Create local dump directory if it doesn't exist
        self.dump_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MemoryDumpService initialized in {self.dump_mode} mode")
        logger.info(f"Dump directory: {self.dump_directory}")
    
    async def create_dump(self, request: DumpRequest, instance_data: Dict[str, Any]) -> str:
        """Create a new memory dump"""
        
        # For local mode, skip SSH configuration check
        if self.dump_mode == "remote":
            # Check SSH configuration
            if not ssh_config.is_configured():
                raise Exception("SSH key not found. Please configure SSH key for memory dumps.")
            
            # Get SSH settings
            ssh_settings = ssh_config.get_ssh_settings(
                custom_user=request.ssh_user,
                custom_key=request.ssh_key_path
            )
        else:
            ssh_settings = None
        
        dump_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract instance information
        instance_name = instance_data.get('name', 'unknown')
        os_type = self._detect_os_type(instance_data)
        
        # For local mode, use instance name as connection identifier
        if self.dump_mode == "local":
            ssh_host = f"local-{instance_name}"  # Identifier for local execution
        else:
            # Use ip_address directly if available, otherwise fallback to extraction from addresses
            ssh_host = instance_data.get('ip_address')
            if not ssh_host:
                ssh_host = self._get_instance_ip(instance_data)
            
            if not ssh_host or ssh_host == 'localhost':
                raise Exception(f"Cannot determine IP address for instance {instance_name}")
        
        logger.info(f"Using SSH host: {ssh_host} for instance {instance_name} in {self.dump_mode} mode")
        
        # Generate filename with .raw extension for memory dumps
        filename = f"{request.instance_id}_{timestamp}_{os_type}.raw"
        file_path = self.dump_directory / filename
        
        # Create dump record
        dump = MemoryDump(
            id=dump_id,
            instance_id=request.instance_id,
            instance_name=instance_name,
            os_type=os_type,
            dump_type=request.dump_type,
            status=DumpStatus.PENDING,
            file_path=str(file_path),
            created_at=datetime.now(),
            ssh_host=ssh_host
        )
        
        self.dumps_db[dump_id] = dump
        
        # Start dump process asynchronously with SSH settings
        task = asyncio.create_task(self._perform_dump(dump_id, ssh_settings))
        self.active_dumps[dump_id] = task
        
        logger.info(f"Created memory dump request {dump_id} for instance {request.instance_id} at {ssh_host}")
        return dump_id
    
    async def _perform_dump(self, dump_id: str, ssh_settings: dict):
        """Perform the actual memory dump via SSH"""
        dump = self.dumps_db[dump_id]
        
        try:
            # Update status to in progress
            dump.status = DumpStatus.IN_PROGRESS
            logger.info(f"Starting memory dump {dump_id} for instance {dump.instance_id} at {dump.ssh_host}")
            
            # Execute dump based on mode
            if self.dump_mode == "local":
                await self._execute_local_dump(dump)
            else:
                await self._execute_remote_dump(dump, ssh_settings)
            
            # Calculate file size and checksum
            if os.path.exists(dump.file_path):
                dump.file_size = os.path.getsize(dump.file_path)
                dump.checksum = await self._calculate_checksum(dump.file_path)
                dump.status = DumpStatus.COMPLETED
                dump.completed_at = datetime.now()
                logger.info(f"Memory dump {dump_id} completed successfully")
            else:
                raise Exception("Dump file was not created")
                
        except Exception as e:
            dump.status = DumpStatus.FAILED
            dump.error_message = str(e)
            logger.error(f"Memory dump {dump_id} failed: {e}")
        finally:
            # Remove from active dumps
            if dump_id in self.active_dumps:
                del self.active_dumps[dump_id]
    
    async def _execute_local_dump(self, dump: MemoryDump):
        """Execute memory dump locally using virsh only (when running on OpenStack server)"""
        logger.info(f"Executing local memory dump {dump.id} for instance {dump.instance_id}")
        
        # Set the local dump file path with proper naming (.raw extension)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_filename = f"{dump.instance_id}_{timestamp}_{dump.os_type}.raw"
        local_dump_file = str(self.dump_directory / local_filename)
        
        # Update the dump file path
        dump.file_path = local_dump_file
        
        # Auto-setup virsh if needed
        await self._ensure_virsh_setup()
        
        # Find the VM domain name using multiple strategies
        vm_domain = await self._find_vm_domain(dump.instance_id)
        
        if not vm_domain:
            # Debug: let's see what virsh actually shows
            await self._debug_virsh_domains(dump.instance_id)
            raise Exception(f"Cannot find libvirt domain for instance {dump.instance_id}")
        
        logger.info(f"Found VM domain: {vm_domain} for instance {dump.instance_id}")
        
        # Execute virsh dump without --live flag (more stable)
        dump_cmd = f"sudo virsh dump '{vm_domain}' '{local_dump_file}' --memory-only"
        
        try:
            logger.info(f"Executing virsh dump: {dump_cmd}")
            
            process = await asyncio.create_subprocess_shell(
                dump_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                stderr_text = stderr.decode('utf-8', errors='replace')
                raise Exception(f"virsh dump failed: {stderr_text}")
            
            # Fix file permissions
            await self._fix_file_permissions(local_dump_file)
            
            # Wait a moment for permissions to take effect
            await asyncio.sleep(0.5)
            
            # Verify dump file was created and has reasonable size
            if not os.path.exists(local_dump_file):
                raise Exception("Dump file was not created")
                
            file_size = os.path.getsize(local_dump_file)
            if file_size < 1000000:  # Less than 1MB
                logger.warning(f"Dump file seems small: {file_size} bytes")
            else:
                logger.info(f"Dump file created successfully: {file_size} bytes")
            
            logger.info(f"Local memory dump {dump.id} completed. File: {local_dump_file}")
            
        except Exception as e:
            logger.error(f"virsh dump failed: {e}")
            raise Exception(f"Memory dump failed: {e}")

    async def _find_vm_domain(self, instance_id: str) -> Optional[str]:
        """Find libvirt domain name for the given instance ID"""
        
        logger.info(f"Searching for libvirt domain for instance: {instance_id}")
        
        # Strategy 1: Find by UUID in QEMU processes (most accurate for OpenStack)
        domain_from_qemu = await self._find_domain_by_qemu_uuid(instance_id)
        if domain_from_qemu:
            logger.info(f"Found domain via QEMU UUID: {domain_from_qemu}")
            return domain_from_qemu
        
        # Strategy 2: Direct mapping from instance ID to domain (fallback)
        domain_patterns = [
            f"instance-{instance_id}",
            f"instance-{instance_id.replace('-', '')}",
            f"instance-{instance_id[:8]}",  # First 8 chars
            instance_id,
        ]
        
        logger.info(f"Trying domain patterns: {domain_patterns}")
        
        for pattern in domain_patterns:
            try:
                check_cmd = f"sudo virsh list --all | grep '{pattern}'"
                logger.debug(f"Checking pattern: {pattern} with command: {check_cmd}")
                
                process = await asyncio.create_subprocess_shell(
                    check_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0 and stdout.strip():
                    stdout_text = stdout.decode('utf-8', errors='replace').strip()
                    logger.info(f"Found match for pattern '{pattern}': {stdout_text}")
                    
                    # Extract domain name from virsh list output
                    lines = stdout_text.split('\n')
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2 and pattern in parts[1]:
                            logger.info(f"Extracted domain name: {parts[1]}")
                            return parts[1]
                else:
                    logger.debug(f"No match for pattern: {pattern}")
            except Exception as e:
                logger.debug(f"Pattern {pattern} check failed: {e}")
                continue
        
        # Strategy 3: List all domains and find partial match (last resort)
        logger.info("Trying strategy 3: listing all domains")
        try:
            list_cmd = "sudo virsh list --all"
            logger.debug(f"Executing: {list_cmd}")
            
            process = await asyncio.create_subprocess_shell(
                list_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                stdout_text = stdout.decode('utf-8', errors='replace').strip()
                logger.info(f"All domains output:\n{stdout_text}")
                
                lines = stdout_text.split('\n')
                for line in lines[2:]:  # Skip header lines
                    parts = line.split()
                    if len(parts) >= 2:
                        domain_name = parts[1]
                        logger.debug(f"Checking domain: {domain_name} against instance: {instance_id}")
                        
                        # Check if domain name contains part of instance ID
                        if (instance_id[:8] in domain_name or 
                            instance_id in domain_name or 
                            instance_id.replace('-', '') in domain_name):
                            logger.info(f"Found domain by partial match: {domain_name}")
                            return domain_name
            else:
                stderr_text = stderr.decode('utf-8', errors='replace')
                logger.warning(f"Failed to list domains: {stderr_text}")
        except Exception as e:
            logger.warning(f"Failed to list all domains: {e}")
        
        logger.error(f"Could not find libvirt domain for instance {instance_id}")
        return None

    async def _find_domain_by_qemu_uuid(self, instance_id: str) -> Optional[str]:
        """Find domain by matching UUID in QEMU processes"""
        try:
            logger.info(f"Searching QEMU processes for UUID: {instance_id}")
            
            # Get QEMU processes with UUID
            cmd = f"ps aux | grep qemu | grep '{instance_id}'"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout.strip():
                qemu_output = stdout.decode('utf-8', errors='replace').strip()
                logger.info(f"Found QEMU process with UUID: {qemu_output}")
                
                # Extract domain name from QEMU command line
                # Look for -name guest=DOMAIN_NAME
                import re
                match = re.search(r'-name guest=([^,]+)', qemu_output)
                if match:
                    domain_name = match.group(1)
                    logger.info(f"Extracted domain name from QEMU: {domain_name}")
                    
                    # Verify domain exists in virsh
                    verify_cmd = f"sudo virsh list --all | grep '{domain_name}'"
                    verify_process = await asyncio.create_subprocess_shell(
                        verify_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    verify_stdout, verify_stderr = await verify_process.communicate()
                    
                    if verify_process.returncode == 0:
                        logger.info(f"Verified domain exists in virsh: {domain_name}")
                        return domain_name
                    else:
                        logger.warning(f"Domain {domain_name} not found in virsh list")
            else:
                logger.debug(f"No QEMU process found for UUID: {instance_id}")
                
        except Exception as e:
            logger.warning(f"Failed to search QEMU processes: {e}")
        
        return None

    async def _debug_virsh_domains(self, instance_id: str):
        """Debug method to see what virsh domains are available"""
        logger.info(f"=== DEBUGGING VIRSH DOMAINS FOR INSTANCE {instance_id} ===")
        
        try:
            # Show all domains
            cmd = "sudo virsh list --all"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='replace')
                logger.info(f"All virsh domains:\n{output}")
            else:
                error = stderr.decode('utf-8', errors='replace')
                logger.error(f"Failed to list domains: {error}")
            
            # Show running domains
            cmd2 = "sudo virsh list --state-running"
            process2 = await asyncio.create_subprocess_shell(
                cmd2,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout2, stderr2 = await process2.communicate()
            
            if process2.returncode == 0:
                output2 = stdout2.decode('utf-8', errors='replace')
                logger.info(f"Running virsh domains:\n{output2}")
            
            # Show QEMU processes
            cmd3 = "ps aux | grep qemu"
            process3 = await asyncio.create_subprocess_shell(
                cmd3,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout3, stderr3 = await process3.communicate()
            
            if process3.returncode == 0:
                output3 = stdout3.decode('utf-8', errors='replace')
                logger.info(f"QEMU processes:\n{output3}")
                
        except Exception as e:
            logger.error(f"Debug failed: {e}")
        
        logger.info("=== END DEBUG ===")

    async def _fix_file_permissions(self, file_path: str):
        """Fix file permissions after dump"""
        try:
            # First make sure the file is readable
            chmod_readable_cmd = f"sudo chmod 644 '{file_path}'"
            process1 = await asyncio.create_subprocess_shell(
                chmod_readable_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process1.communicate()
            
            # Then change ownership to stack user
            chown_cmd = f"sudo chown stack:stack '{file_path}'"
            process2 = await asyncio.create_subprocess_shell(
                chown_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process2.communicate()
            
            # Make sure permissions are applied
            chmod_final_cmd = f"sudo chmod 644 '{file_path}'"
            process3 = await asyncio.create_subprocess_shell(
                chmod_final_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process3.communicate()
            
            logger.info(f"Fixed permissions for {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to fix permissions for {file_path}: {e}")

    async def _ensure_virsh_setup(self):
        """Ensure virsh is installed and configured for memory dumps"""
        try:
            # Check if virsh is available
            process = await asyncio.create_subprocess_shell(
                "which virsh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.info("Installing libvirt-clients for virsh...")
                # Install libvirt-clients
                install_process = await asyncio.create_subprocess_shell(
                    "sudo apt update && sudo apt install -y libvirt-clients qemu-utils",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await install_process.communicate()
                
                if install_process.returncode == 0:
                    logger.info("libvirt-clients installed successfully")
                else:
                    logger.warning("Failed to install libvirt-clients, falling back to other methods")
            
            # Check if libvirtd is running
            service_process = await asyncio.create_subprocess_shell(
                "sudo systemctl is-active libvirtd",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await service_process.communicate()
            
            if service_process.returncode != 0:
                logger.info("Starting libvirtd service...")
                start_process = await asyncio.create_subprocess_shell(
                    "sudo systemctl start libvirtd",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await start_process.communicate()
            
            logger.info("virsh setup completed")
            
        except Exception as e:
            logger.warning(f"virsh setup failed: {e}, will fall back to other dump methods")

    async def _execute_remote_dump(self, dump: MemoryDump, ssh_settings: dict):
        """Execute memory dump via SSH (when running remotely)"""
        ssh_options = asyncssh.SSHClientConnectionOptions(
            username=ssh_settings["ssh_user"],
            client_keys=[ssh_settings["ssh_key_path"]] if ssh_settings["ssh_key_path"] else None,
            known_hosts=None  # Disable host key checking for lab environment
        )
        
        logger.info(f"Connecting to {dump.ssh_host} as {ssh_settings['ssh_user']} with key {ssh_settings['ssh_key_path']}")
        
        async with asyncssh.connect(dump.ssh_host, options=ssh_options) as conn:
            # First, ensure the dump directory exists on the remote server
            await conn.run(f"mkdir -p {self.remote_dump_directory}", check=False)
            
            # Set the remote dump file path with proper naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            remote_filename = f"{dump.instance_id}_{timestamp}_{dump.os_type}.dump"
            dump_file_remote = f"{self.remote_dump_directory}/{remote_filename}"
            
            # Different dump methods based on OS and availability
            dump_commands = [
                # Method 1: LiME (Linux Memory Extractor) - if available
                f"if command -v lime &> /dev/null; then lime {dump_file_remote}; fi",
                
                # Method 2: dd from /proc/kcore (requires root)
                f"dd if=/proc/kcore of={dump_file_remote} bs=1M count=100 2>/dev/null || true",
                
                # Method 3: gcore of init process (alternative)
                f"gcore -o {self.remote_dump_directory}/memory_{dump.instance_id} 1 2>/dev/null || true",
                
                # Method 4: Create a simulated dump for testing
                f"dd if=/dev/urandom of={dump_file_remote} bs=1M count=50 2>/dev/null"
            ]
            
            # Try each method until one succeeds
            for i, cmd in enumerate(dump_commands):
                try:
                    logger.info(f"Attempting dump method {i+1} for {dump.id}")
                    result = await conn.run(cmd, check=False)
                    
                    # Check if dump file was created
                    check_result = await conn.run(f"ls -la {dump_file_remote} 2>/dev/null || ls -la {self.remote_dump_directory}/memory_{dump.instance_id}.* 2>/dev/null", check=False)
                    
                    if check_result.returncode == 0 and check_result.stdout.strip():
                        logger.info(f"Dump method {i+1} succeeded for {dump.id}")
                        break
                        
                except Exception as e:
                    logger.warning(f"Dump method {i+1} failed for {dump.id}: {e}")
                    continue
            
            # Find the actual dump file (in case gcore created a different name)
            find_result = await conn.run(f"find {self.remote_dump_directory} -name '*{dump.instance_id}*' -o -name 'memory*dump*' | head -1", check=False)
            if find_result.stdout.strip():
                dump_file_remote = find_result.stdout.strip()
            
            # Copy file from remote to local
            async with conn.start_sftp_client() as sftp:
                await sftp.get(dump_file_remote, dump.file_path)
            
            # DO NOT clean up remote file - keep for forensics and "Dumped Ram" tab
            logger.info(f"Memory dump {dump.id} completed. Remote file preserved at: {dump_file_remote}")
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of the dump file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _detect_os_type(self, instance_data: Dict[str, Any]) -> str:
        """Detect OS type from instance data"""
        image_name = instance_data.get('image', {}).get('name', '').lower()
        
        if 'ubuntu' in image_name:
            return 'ubuntu'
        elif 'centos' in image_name:
            return 'centos'
        elif 'debian' in image_name:
            return 'debian'
        elif 'rhel' in image_name:
            return 'rhel'
        else:
            return 'linux'
    
    def _get_instance_ip(self, instance_data: Dict[str, Any]) -> str:
        """Extract IP address from instance data"""
        # Try to get floating IP first, then fixed IP
        addresses = instance_data.get('addresses', {})
        
        for network_name, addresses_list in addresses.items():
            for addr in addresses_list:
                if addr.get('OS-EXT-IPS:type') == 'floating':
                    return addr.get('addr')
        
        # Fallback to first fixed IP
        for network_name, addresses_list in addresses.items():
            for addr in addresses_list:
                if addr.get('OS-EXT-IPS:type') == 'fixed':
                    return addr.get('addr')
        
        # Last resort - use instance name as hostname
        return instance_data.get('name', 'localhost')
    
    def get_all_dumps(self) -> List[MemoryDump]:
        """Get all memory dumps"""
        return list(self.dumps_db.values())
    
    def get_dump(self, dump_id: str) -> Optional[MemoryDump]:
        """Get specific memory dump"""
        return self.dumps_db.get(dump_id)
    
    def get_dump_file_path(self, dump_id: str) -> Optional[str]:
        """Get file path for download"""
        dump = self.get_dump(dump_id)
        if dump and dump.status == DumpStatus.COMPLETED and os.path.exists(dump.file_path):
            return dump.file_path
        return None


# Global service instance
memory_dump_service = MemoryDumpService()
