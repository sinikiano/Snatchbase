#!/usr/bin/env python3
"""
Service Manager
Manages and monitors all Snatchbase services with health checks and auto-restart
"""
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from launcher.config import ServiceConfig

# Configure logging
ServiceConfig.ensure_directories()
logging.basicConfig(
    level=getattr(logging, ServiceConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ServiceConfig.LOG_DIR / "service_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a service"""
    name: str
    script: str
    enabled: bool
    process: Optional[subprocess.Popen] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    health_check_url: Optional[str] = None


class ServiceManager:
    """Manages multiple services with health monitoring"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.running = False
        self.launcher_dir = Path(__file__).parent
        
    def register_service(self, name: str, script: str, enabled: bool, health_check_url: Optional[str] = None):
        """Register a service"""
        self.services[name] = ServiceInfo(
            name=name,
            script=script,
            enabled=enabled,
            health_check_url=health_check_url
        )
    
    def start_service(self, name: str) -> bool:
        """Start a single service"""
        service = self.services.get(name)
        if not service:
            logger.error(f"❌ Service {name} not found")
            return False
        
        if not service.enabled:
            logger.info(f"⏭️  Service {name} is disabled")
            return False
        
        if service.process and service.process.poll() is None:
            logger.warning(f"⚠️  Service {name} is already running")
            return True
        
        try:
            logger.info(f"🚀 Starting {name}...")
            script_path = self.launcher_dir / service.script
            
            # Start the service
            service.process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.launcher_dir.parent
            )
            
            # Wait a moment to ensure it starts
            time.sleep(2)
            
            # Check if it's still running
            if service.process.poll() is None:
                logger.info(f"✅ {name} started successfully (PID: {service.process.pid})")
                return True
            else:
                logger.error(f"❌ {name} failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}", exc_info=True)
            return False
    
    def stop_service(self, name: str) -> bool:
        """Stop a single service"""
        service = self.services.get(name)
        if not service or not service.process:
            return False
        
        try:
            logger.info(f"🛑 Stopping {name}...")
            service.process.terminate()
            
            # Wait for graceful shutdown
            try:
                service.process.wait(timeout=10)
                logger.info(f"✅ {name} stopped")
                return True
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️  {name} didn't stop gracefully, killing...")
                service.process.kill()
                service.process.wait()
                logger.info(f"✅ {name} killed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to stop {name}: {e}", exc_info=True)
            return False
    
    def restart_service(self, name: str) -> bool:
        """Restart a service"""
        service = self.services.get(name)
        if not service:
            return False
        
        # Check restart limits
        if service.last_restart:
            time_since_restart = (datetime.now() - service.last_restart).total_seconds()
            if time_since_restart < ServiceConfig.SERVICE_RESTART_DELAY:
                logger.warning(f"⚠️  Too soon to restart {name}, waiting...")
                return False
        
        if service.restart_count >= ServiceConfig.MAX_RESTART_ATTEMPTS:
            logger.error(f"❌ {name} has exceeded max restart attempts ({ServiceConfig.MAX_RESTART_ATTEMPTS})")
            return False
        
        logger.info(f"🔄 Restarting {name}...")
        self.stop_service(name)
        time.sleep(ServiceConfig.SERVICE_RESTART_DELAY)
        
        if self.start_service(name):
            service.restart_count += 1
            service.last_restart = datetime.now()
            return True
        return False
    
    def check_service_health(self, name: str) -> bool:
        """Check if a service is healthy"""
        service = self.services.get(name)
        if not service or not service.enabled:
            return True
        
        # Check if process is running
        if not service.process or service.process.poll() is not None:
            logger.warning(f"⚠️  {name} is not running")
            return False
        
        # If health check URL is provided, check it
        if service.health_check_url:
            try:
                import requests
                response = requests.get(service.health_check_url, timeout=5)
                if response.status_code == 200:
                    return True
                else:
                    logger.warning(f"⚠️  {name} health check failed (status: {response.status_code})")
                    return False
            except Exception as e:
                logger.warning(f"⚠️  {name} health check error: {e}")
                return False
        
        return True
    
    def health_check_loop(self):
        """Continuously monitor service health"""
        while self.running:
            for name, service in self.services.items():
                if service.enabled and not self.check_service_health(name):
                    logger.warning(f"⚠️  {name} failed health check, attempting restart...")
                    self.restart_service(name)
            
            time.sleep(ServiceConfig.HEALTH_CHECK_INTERVAL)
    
    def start_all(self):
        """Start all enabled services"""
        logger.info("🚀 Starting all enabled services...")
        
        for name in self.services:
            self.start_service(name)
        
        logger.info("✅ All services started")
    
    def stop_all(self):
        """Stop all services"""
        logger.info("🛑 Stopping all services...")
        self.running = False
        
        for name in self.services:
            self.stop_service(name)
        
        logger.info("✅ All services stopped")
    
    def run(self):
        """Run the service manager"""
        self.running = True
        
        # Register signal handlers
        def signal_handler(signum, frame):
            logger.info(f"📨 Received signal {signum}, shutting down...")
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start all services
        self.start_all()
        
        # Run health check loop
        try:
            self.health_check_loop()
        except Exception as e:
            logger.error(f"❌ Health check loop failed: {e}", exc_info=True)
            self.stop_all()
            sys.exit(1)


def main():
    """Main entry point"""
    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║         Snatchbase Service Manager v2.0                      ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    
    manager = ServiceManager()
    
    # Register services
    manager.register_service(
        name="API",
        script="api_service.py",
        enabled=True,
        health_check_url=f"http://localhost:{ServiceConfig.API_PORT}/health"
    )
    
    manager.register_service(
        name="Telegram Bot",
        script="telegram_service.py",
        enabled=ServiceConfig.TELEGRAM_ENABLED and ServiceConfig.is_telegram_configured()
    )
    
    manager.register_service(
        name="File Watcher",
        script="file_watcher_service.py",
        enabled=ServiceConfig.FILE_WATCHER_ENABLED
    )
    
    manager.register_service(
        name="Wallet Checker",
        script="wallet_checker_service.py",
        enabled=ServiceConfig.WALLET_CHECKER_ENABLED
    )
    
    # Show configuration
    logger.info("\n📋 Service Configuration:")
    for name, service in manager.services.items():
        status = "✅ Enabled" if service.enabled else "⏭️  Disabled"
        logger.info(f"   • {name}: {status}")
    
    logger.info("\n🔧 Starting services...\n")
    
    # Run the manager
    manager.run()


if __name__ == "__main__":
    main()
