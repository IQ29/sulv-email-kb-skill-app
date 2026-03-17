#!/bin/bash
# Full Test Suite for SULV Email + KB Integration
# Run this after authentication is complete

set -e  # Exit on error

echo "================================================================"
echo "SULV Email + KB Full Test Suite"
echo "================================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to run test with status
run_test() {
    echo ""
    echo "=== $1 ==="
    if python3 "$2" > /tmp/test_output.log 2>&1; then
        print_status 0 "$1 completed successfully"
        return 0
    else
        print_status 1 "$1 failed"
        echo "Error output:"
        cat /tmp/test_output.log | tail -20
        return 1
    fi
}

# Check if we're in the right directory
if [ ! -f "TEST_EXECUTION_PLAN.md" ]; then
    echo "Error: Please run from the workspace directory"
    exit 1
fi

echo "Starting comprehensive test suite..."
echo "Timestamp: $(date)"
echo ""

# Phase 1: Pre-flight checks
echo "Phase 1: Pre-flight Checks"
echo "-------------------------"

# Check Python
if command -v python3 > /dev/null 2>&1; then
    print_status 0 "Python 3 is available"
else
    print_status 1 "Python 3 is not available"
    exit 1
fi

# Check mcporter
if command -v mcporter > /dev/null 2>&1; then
    print_status 0 "mcporter is available"
else
    print_status 1 "mcporter is not available"
    exit 1
fi

# Check gog
if command -v gog > /dev/null 2>&1; then
    print_status 0 "gog CLI is available"
else
    print_status 1 "gog CLI is not available"
fi

# Phase 2: Run test scripts
echo ""
echo "Phase 2: Test Execution"
echo "----------------------"

# Test 1: Check current status
run_test "Status Check" "check_test_status.py"

# Test 2: SULV skill workflow
run_test "SULV Skill Test" "test_sulv_skill_workflow.py"

# Test 3: gog installation verification
run_test "gog Integration Test" "test_gog_installation.py"

# Test 4: 100 Email Scale Test
run_test "100 Email Scale Test" "test_email_kb_integration.py"

# Phase 3: Generate summary
echo ""
echo "Phase 3: Test Summary"
echo "-------------------"

# Check for test reports
if [ -f "test_reports/sulv_skill_test_report.json" ]; then
    echo -e "${GREEN}✓${NC} Test report generated: test_reports/sulv_skill_test_report.json"
    
    # Extract key metrics
    echo ""
    echo "Key Metrics:"
    echo "-----------"
    
    # Check test data
    if [ -f "test_data/test_report.json" ]; then
        EMAILS=$(python3 -c "import json; data=json.load(open('test_data/test_report.json')); print(data.get('summary', {}).get('num_emails', 'N/A'))")
        ATTACHMENTS=$(python3 -c "import json; data=json.load(open('test_data/test_report.json')); print(data.get('summary', {}).get('total_attachments', 'N/A'))")
        KB_ENTRIES=$(python3 -c "import json; data=json.load(open('test_data/test_report.json')); print(data.get('kb_processing', {}).get('kb_entries_created', 'N/A'))")
        
        echo "Emails processed: $EMAILS"
        echo "Attachments handled: $ATTACHMENTS"
        echo "KB entries created: $KB_ENTRIES"
    fi
else
    echo -e "${YELLOW}⚠${NC} No test report found"
fi

# Phase 4: Next steps
echo ""
echo "Phase 4: Next Steps"
echo "------------------"

echo "1. Review test reports in:"
echo "   - test_reports/sulv_skill_test_report.json"
echo "   - test_data/test_report.json"
echo "   - test_workflow/workflow_simulation.json"

echo ""
echo "2. Check for any error logs:"
if [ -d "logs" ]; then
    echo "   Logs available in: logs/"
    ls -la logs/ 2>/dev/null || echo "   (no log files)"
else
    echo "   No logs directory found"
fi

echo ""
echo "3. For real email testing, run:"
echo "   cd skills/sulv-google-workspace-hybrid/scripts"
echo "   python3 email_sync.py --query 'from:admin_auto@sulv.com.au newer_than:1d' --max-results 5"

echo ""
echo "4. To test KB integration with real data:"
echo "   cd enterprise-kb"
echo "   python3 main.py --help"

echo ""
echo "================================================================"
echo "Test Suite Complete!"
echo "================================================================"
echo ""
echo "Summary:"
echo "--------"
echo "All tests have been executed. Check the output above for any failures."
echo ""
echo "For detailed results, review the generated JSON reports."
echo ""
echo "Next: Proceed to real email testing when ready."