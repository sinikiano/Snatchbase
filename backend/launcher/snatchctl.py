#!/usr/bin/env python3
"""
Snatchbase Service Control CLI
Simple command-line interface for managing Snatchbase services
"""
import sys
import subprocess
from pathlib import Path

LAUNCHER_DIR = Path(__file__).parent


def print_help():
    """Print help information"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Snatchbase Service Control v2.0                    ║
╚══════════════════════════════════════════════════════════════╝

Usage: python3 snatchctl.py [command] [service]

Commands:
  start [service]   - Start all services or a specific service
  stop              - Stop all services
  restart [service] - Restart all services or a specific service
  status            - Show service status
  logs [service]    - Show logs for a service

Services:
  all               - All services (default)
  api               - FastAPI server
  telegram          - Telegram bot
  file-watcher      - ZIP file ingestion
  wallet-checker    - Wallet balance checker

Examples:
  python3 snatchctl.py start              # Start all services
  python3 snatchctl.py start api          # Start only API
  python3 snatchctl.py logs api           # View API logs
  python3 snatchctl.py restart telegram   # Restart Telegram bot
  python3 snatchctl.py status             # Check service status
    """)


def start_service(service="all"):
    """Start a service"""
    if service == "all":
        print("🚀 Starting all services...")
        subprocess.run([sys.executable, str(LAUNCHER_DIR / "service_manager.py")])
    elif service == "api":
        print("🚀 Starting API service...")
        subprocess.run([sys.executable, str(LAUNCHER_DIR / "api_service.py")])
    elif service == "telegram":
        print("🚀 Starting Telegram bot...")
        subprocess.run([sys.executable, str(LAUNCHER_DIR / "telegram_service.py")])
    elif service == "file-watcher":
        print("🚀 Starting file watcher...")
        subprocess.run([sys.executable, str(LAUNCHER_DIR / "file_watcher_service.py")])
    elif service == "wallet-checker":
        print("🚀 Starting wallet checker...")
        subprocess.run([sys.executable, str(LAUNCHER_DIR / "wallet_checker_service.py")])
    else:
        print(f"❌ Unknown service: {service}")
        print_help()


def show_logs(service="all"):
    """Show logs for a service"""
    log_dir = LAUNCHER_DIR.parent / "logs"
    
    if service == "all":
        print("📝 Viewing all service logs (Ctrl+C to exit)...")
        subprocess.run(["tail", "-f", str(log_dir / "*.log")])
    elif service == "api":
        subprocess.run(["tail", "-f", str(log_dir / "api.log")])
    elif service == "telegram":
        subprocess.run(["tail", "-f", str(log_dir / "telegram_bot.log")])
    elif service == "file-watcher":
        subprocess.run(["tail", "-f", str(log_dir / "file_watcher.log")])
    elif service == "wallet-checker":
        subprocess.run(["tail", "-f", str(log_dir / "wallet_checker.log")])
    elif service == "manager":
        subprocess.run(["tail", "-f", str(log_dir / "service_manager.log")])
    else:
        print(f"❌ Unknown service: {service}")


def show_status():
    """Show service status"""
    print("📊 Snatchbase Service Status\n")
    subprocess.run(["ps", "aux"], stdout=subprocess.PIPE, text=True)
    result = subprocess.run(
        ["ps", "aux"], 
        stdout=subprocess.PIPE, 
        text=True, 
        check=True
    )
    
    services = {
        "Service Manager": "service_manager.py",
        "API Server": "api_service.py",
        "Telegram Bot": "telegram_service.py",
        "File Watcher": "file_watcher_service.py",
        "Wallet Checker": "wallet_checker_service.py",
    }
    
    for name, script in services.items():
        if script in result.stdout:
            print(f"  ✅ {name}: Running")
        else:
            print(f"  ⏹️  {name}: Stopped")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    service = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    if command == "help" or command == "--help" or command == "-h":
        print_help()
    elif command == "start":
        start_service(service)
    elif command == "logs":
        show_logs(service)
    elif command == "status":
        show_status()
    else:
        print(f"❌ Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
