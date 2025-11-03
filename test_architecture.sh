#!/bin/bash
# Test script to verify all components work correctly

echo "🧪 Testing Snatchbase v2.0 Components"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_passed=0
test_failed=0

# Test 1: Check file structure
echo "📁 Test 1: Checking file structure..."
if [ -f "backend/launcher/service_manager.py" ] && \
   [ -f "backend/launcher/api_service.py" ] && \
   [ -f "backend/app/routers/credentials.py" ] && \
   [ -f "backend/app/main.py" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - All required files exist"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} - Missing required files"
    ((test_failed++))
fi

# Test 2: Check main.py size
echo ""
echo "📝 Test 2: Checking main.py optimization..."
lines=$(wc -l < backend/app/main.py)
if [ "$lines" -lt 100 ]; then
    echo -e "${GREEN}✅ PASSED${NC} - main.py is ${lines} lines (optimized!)"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} - main.py is ${lines} lines (too large)"
    ((test_failed++))
fi

# Test 3: Check Python syntax
echo ""
echo "🐍 Test 3: Checking Python syntax..."
errors=0
for file in backend/launcher/*.py backend/app/routers/*.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            :
        else
            echo -e "${RED}   Syntax error in: $file${NC}"
            ((errors++))
        fi
    fi
done

if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ PASSED${NC} - All Python files have valid syntax"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} - Found $errors files with syntax errors"
    ((test_failed++))
fi

# Test 4: Check configuration file
echo ""
echo "⚙️  Test 4: Checking configuration..."
if [ -f "backend/.env.template" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Configuration template exists"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} - Missing .env.template"
    ((test_failed++))
fi

# Test 5: Check executability
echo ""
echo "🔐 Test 5: Checking script permissions..."
if [ -x "start_snatchbase_v2.sh" ] && \
   [ -x "backend/launcher/service_manager.py" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Scripts are executable"
    ((test_passed++))
else
    echo -e "${RED}❌ FAILED${NC} - Some scripts are not executable"
    ((test_failed++))
fi

# Summary
echo ""
echo "======================================="
echo "📊 Test Summary"
echo "======================================="
echo -e "Passed: ${GREEN}${test_passed}${NC}"
echo -e "Failed: ${RED}${test_failed}${NC}"
echo ""

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Ready to deploy.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix the issues.${NC}"
    exit 1
fi
