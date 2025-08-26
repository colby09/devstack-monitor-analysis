"""
Health monitoring service
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.services.openstack import OpenStackClient
from app.services.websocket import WebSocketManager

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Health monitoring service"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.openstack_client = OpenStackClient()
        self.monitoring = False
        self.monitor_task = None
    
    async def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system data
                data = await self._collect_system_data()
                
                # Send updates via WebSocket
                await self.websocket_manager.broadcast(data)
                
                # Wait for next interval
                await asyncio.sleep(settings.MONITOR_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _collect_system_data(self) -> Dict[str, Any]:
        """Collect system health data"""
        try:
            # Get instances and services data
            instances = await self.openstack_client.get_instances()
            services = await self.openstack_client.get_services()
            
            # Calculate statistics
            instance_stats = self._calculate_instance_stats(instances)
            service_stats = self._calculate_service_stats(services)
            
            # Generate system metrics
            system_metrics = self._generate_system_metrics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "instances": {
                    "total": len(instances),
                    "active": len([i for i in instances if i.status == "active"]),
                    "stats": instance_stats,
                    "list": [
                        {
                            "id": i.id,
                            "name": i.name,
                            "status": i.status,
                            "cpu_usage": i.cpu_usage,
                            "memory_usage": i.memory_usage
                        } for i in instances[:5]  # Send only first 5 for real-time updates
                    ]
                },
                "services": {
                    "total": len(services),
                    "healthy": len([s for s in services if s.status == "healthy"]),
                    "stats": service_stats,
                    "list": [
                        {
                            "name": s.name,
                            "status": s.status,
                            "response_time": s.response_time
                        } for s in services[:5]
                    ]
                },
                "system": system_metrics
            }
            
        except Exception as e:
            logger.error(f"Error collecting system data: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _calculate_instance_stats(self, instances) -> Dict[str, Any]:
        """Calculate instance statistics"""
        if not instances:
            return {"avg_cpu": 0, "avg_memory": 0, "health_score": 0}
        
        active_instances = [i for i in instances if i.status == "active"]
        
        if not active_instances:
            return {"avg_cpu": 0, "avg_memory": 0, "health_score": 0}
        
        avg_cpu = sum(i.cpu_usage for i in active_instances) / len(active_instances)
        avg_memory = sum(i.memory_usage for i in active_instances) / len(active_instances)
        
        # Calculate health score (0-100)
        health_score = 100 - (avg_cpu * 0.4 + avg_memory * 0.6)
        health_score = max(0, min(100, health_score))
        
        return {
            "avg_cpu": round(avg_cpu, 1),
            "avg_memory": round(avg_memory, 1),
            "health_score": round(health_score, 1)
        }
    
    def _calculate_service_stats(self, services) -> Dict[str, Any]:
        """Calculate service statistics"""
        if not services:
            return {"avg_response_time": 0, "availability": 0}
        
        healthy_services = [s for s in services if s.status == "healthy"]
        
        avg_response_time = 0
        if healthy_services:
            avg_response_time = sum(s.response_time for s in healthy_services) / len(healthy_services)
        
        availability = (len(healthy_services) / len(services)) * 100
        
        return {
            "avg_response_time": round(avg_response_time, 1),
            "availability": round(availability, 1)
        }
    
    def _generate_system_metrics(self) -> Dict[str, Any]:
        """Generate system performance metrics"""
        import random
        
        return {
            "cpu_usage": round(random.uniform(40, 80), 1),
            "memory_usage": round(random.uniform(50, 85), 1),
            "disk_usage": round(random.uniform(30, 70), 1),
            "network_io": round(random.uniform(1, 10), 2),
            "uptime": "2d 14h 32m",
            "load_average": round(random.uniform(0.5, 2.0), 2)
        }