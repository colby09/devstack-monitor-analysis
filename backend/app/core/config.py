"""
Application configuration settings - FIXED VERSION
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    
    # OpenStack settings with proper defaults
    OS_AUTH_URL: str = "http://localhost/identity/v3"  # Changed for Linux environment
    OS_PROJECT_NAME: str = "admin"
    OS_USERNAME: str = "admin"
    OS_PASSWORD: str = "secret"
    OS_USER_DOMAIN_NAME: str = "Default"
    OS_PROJECT_DOMAIN_NAME: str = "Default"
    
    # Monitoring settings
    MONITOR_INTERVAL: int = 30  # seconds
    MONITOR_TIMEOUT: int = 10   # seconds
    MONITOR_RETRIES: int = 3
    
    # Alert thresholds
    CPU_THRESHOLD: float = 80.0
    MEMORY_THRESHOLD: float = 85.0
    DISK_THRESHOLD: float = 90.0
    
    # Database settings (SQLite for simplicity)
    DATABASE_URL: str = "sqlite:///./health_monitor.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Memory dump settings
    DUMP_MODE: str = "local"  # "local" for running on OpenStack server, "remote" for SSH, "mock" for testing
    DUMP_LOCAL_DIRECTORY: str = "/tmp/ramdump"
    DUMP_REMOTE_DIRECTORY: str = "/tmp/dumps"
    OPENSTACK_HOST: str = "192.168.78.190"  # OpenStack server IP for SSH connections
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Auto-detect DevStack credentials if available
        self._load_devstack_credentials()
    
    def _load_devstack_credentials(self):
        """Load DevStack credentials from environment or openrc file"""
        try:
            # Try to load from current environment first
            if os.getenv('OS_AUTH_URL'):
                self.OS_AUTH_URL = os.getenv('OS_AUTH_URL', self.OS_AUTH_URL)
                self.OS_PROJECT_NAME = os.getenv('OS_PROJECT_NAME', self.OS_PROJECT_NAME)
                self.OS_USERNAME = os.getenv('OS_USERNAME', self.OS_USERNAME)
                self.OS_PASSWORD = os.getenv('OS_PASSWORD', self.OS_PASSWORD)
                self.OS_USER_DOMAIN_NAME = os.getenv('OS_USER_DOMAIN_NAME', self.OS_USER_DOMAIN_NAME)
                self.OS_PROJECT_DOMAIN_NAME = os.getenv('OS_PROJECT_DOMAIN_NAME', self.OS_PROJECT_DOMAIN_NAME)
                return
            
            # Try to source openrc file if environment variables are not set
            openrc_path = "/opt/stack/devstack/openrc"
            if os.path.exists(openrc_path):
                import subprocess
                result = subprocess.run(
                    f"source {openrc_path} admin admin && env | grep ^OS_",
                    shell=True,
                    capture_output=True,
                    text=True,
                    executable='/bin/bash'
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key == 'OS_AUTH_URL':
                                self.OS_AUTH_URL = value
                            elif key == 'OS_PROJECT_NAME':
                                self.OS_PROJECT_NAME = value
                            elif key == 'OS_USERNAME':
                                self.OS_USERNAME = value
                            elif key == 'OS_PASSWORD':
                                self.OS_PASSWORD = value
                            elif key == 'OS_USER_DOMAIN_NAME':
                                self.OS_USER_DOMAIN_NAME = value
                            elif key == 'OS_PROJECT_DOMAIN_NAME':
                                self.OS_PROJECT_DOMAIN_NAME = value
        except Exception as e:
            # If auto-detection fails, use defaults
            pass


# Global settings instance
settings = Settings()