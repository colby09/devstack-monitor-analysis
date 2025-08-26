"""
SSH Configuration for memory dumps
"""

import os
from pathlib import Path
from typing import Optional


class SSHConfig:
    """SSH configuration manager"""
    
    def __init__(self):
        # Default SSH settings
        self.default_ssh_user = "root"
        self.default_ssh_key_path = self._find_default_ssh_key()
        
        # You can override these via environment variables
        self.ssh_user = os.getenv("DUMP_SSH_USER", self.default_ssh_user)
        self.ssh_key_path = os.getenv("DUMP_SSH_KEY_PATH", self.default_ssh_key_path)
    
    def _find_default_ssh_key(self) -> Optional[str]:
        """Find default SSH key in common locations"""
        possible_keys = [
            # Custom location for your key
            Path("C:/temp/ssh_keys/openstack_key"),
            # Windows common locations
            Path.home() / ".ssh" / "id_rsa",
            Path.home() / ".ssh" / "id_ed25519",
            # OpenStack common key names
            Path.home() / ".ssh" / "openstack_key",
            Path.home() / ".ssh" / "devstack_key",
            # Current directory
            Path.cwd() / "ssh_keys" / "id_rsa",
            Path.cwd() / "ssh_keys" / "openstack_key"
        ]
        
        for key_path in possible_keys:
            if key_path.exists():
                print(f"Found SSH key: {key_path}")
                return str(key_path)
        
        print("No SSH key found in common locations")
        return None
    
    def get_ssh_settings(self, custom_user: Optional[str] = None, custom_key: Optional[str] = None) -> dict:
        """Get SSH settings with optional overrides"""
        return {
            "ssh_user": custom_user or self.ssh_user,
            "ssh_key_path": custom_key or self.ssh_key_path
        }
    
    def is_configured(self) -> bool:
        """Check if SSH is properly configured"""
        return self.ssh_key_path is not None and Path(self.ssh_key_path).exists()


# Global SSH config instance
ssh_config = SSHConfig()
