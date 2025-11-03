#!/usr/bin/env python3
"""
Integration Validator for Snatchbase v2.0
Validates all service integrations and configurations
"""
import sys
import os
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

def print_test(name, passed, details=""):
    status = f"{GREEN}✅ PASSED{NC}" if passed else f"{RED}❌ FAILED{NC}"
    print(f"{status} - {name}")
    if details and not passed:
        print(f"  {YELLOW}{details}{NC}")
    return 1 if passed else 0

def main():
    print_header("Snatchbase v2.0 Integration Validator")
    
    passed = 0
    failed = 0
    
    # Test 1: File Structure
    print("📁 Validating file structure...")
    required_files = [
        "backend/launcher/__init__.py",
        "backend/launcher/config.py",
        "backend/launcher/service_manager.py",
        "backend/launcher/api_service.py",
        "backend/launcher/telegram_service.py",
        "backend/launcher/file_watcher_service.py",
        "backend/launcher/wallet_checker_service.py",
        "backend/launcher/snatchctl.py",
        "backend/app/main.py",
        "backend/app/routers/__init__.py",
        "backend/app/routers/credentials.py",
        "backend/app/routers/devices.py",
        "backend/app/routers/statistics.py",
        "backend/app/routers/files.py",
        "backend/.env.template",
        "start_snatchbase_v2.sh",
    ]
    
    all_exist = True
    missing = []
    for file in required_files:
        if not Path(file).exists():
            all_exist = False
            missing.append(file)
    
    if all_exist:
        passed += print_test("All required files exist", True)
    else:
        failed += print_test("File structure", False, f"Missing: {', '.join(missing)}")
    
    # Test 2: Import Validation
    print("\n🐍 Validating Python imports...")
    sys.path.insert(0, str(Path("backend").absolute()))
    
    try:
        from launcher import config
        passed += print_test("launcher.config imports", True)
    except Exception as e:
        failed += print_test("launcher.config imports", False, str(e))
    
    try:
        from app.routers import credentials, devices, statistics, files
        passed += print_test("All routers import", True)
    except Exception as e:
        failed += print_test("Router imports", False, str(e))
    
    # Test 3: Configuration Validation
    print("\n⚙️  Validating configuration...")
    try:
        from launcher.config import ServiceConfig
        ServiceConfig.ensure_directories()
        passed += print_test("ServiceConfig functional", True)
    except Exception as e:
        failed += print_test("ServiceConfig", False, str(e))
    
    # Test 4: Main.py Optimization
    print("\n📝 Validating code optimization...")
    main_lines = len(open("backend/app/main.py").readlines())
    if main_lines < 100:
        passed += print_test(f"main.py optimized ({main_lines} lines)", True)
    else:
        failed += print_test(f"main.py size", False, f"Too large: {main_lines} lines")
    
    # Test 5: Executable Permissions
    print("\n🔐 Validating permissions...")
    exec_files = [
        "start_snatchbase_v2.sh",
        "backend/launcher/service_manager.py",
        "backend/launcher/api_service.py",
        "backend/launcher/snatchctl.py",
    ]
    
    all_exec = True
    for file in exec_files:
        if not os.access(file, os.X_OK):
            all_exec = False
            break
    
    if all_exec:
        passed += print_test("All scripts executable", True)
    else:
        failed += print_test("Script permissions", False, "Some scripts not executable")
    
    # Test 6: Router Integration
    print("\n🔗 Validating router integration...")
    try:
        main_content = open("backend/app/main.py").read()
        routers_imported = all([
            "credentials.router" in main_content,
            "devices.router" in main_content,
            "statistics.router" in main_content,
            "files.router" in main_content,
        ])
        
        if routers_imported:
            passed += print_test("All routers integrated in main.py", True)
        else:
            failed += print_test("Router integration", False, "Not all routers included")
    except Exception as e:
        failed += print_test("Router integration check", False, str(e))
    
    # Test 7: Service Manager Configuration
    print("\n🎯 Validating service manager...")
    try:
        manager_content = open("backend/launcher/service_manager.py").read()
        services_registered = all([
            'register_service' in manager_content,
            'API' in manager_content,
            'Telegram Bot' in manager_content,
            'File Watcher' in manager_content,
        ])
        
        if services_registered:
            passed += print_test("Service manager properly configured", True)
        else:
            failed += print_test("Service manager", False, "Not all services registered")
    except Exception as e:
        failed += print_test("Service manager validation", False, str(e))
    
    # Summary
    print_header("Validation Summary")
    print(f"Tests Passed: {GREEN}{passed}{NC}")
    print(f"Tests Failed: {RED}{failed}{NC}")
    print(f"Total Tests:  {passed + failed}")
    print()
    
    if failed == 0:
        print(f"{GREEN}🎉 All validations passed! Architecture is ready!{NC}")
        return 0
    else:
        print(f"{RED}⚠️  Some validations failed. Please fix the issues.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
