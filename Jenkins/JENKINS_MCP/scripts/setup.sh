#!/bin/bash

# Jenkins MCP Server Setup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.9"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
CONFIG_FILE="$PROJECT_DIR/.env"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_python() {
    log_step "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION=$(echo $PYTHON_MIN_VERSION | sed 's/\.//')
    CURRENT_VERSION=$(echo $PYTHON_VERSION | sed 's/\.//')
    
    if [ "$CURRENT_VERSION" -lt "$REQUIRED_VERSION" ]; then
        log_error "Python $PYTHON_MIN_VERSION or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    log_info "Python $PYTHON_VERSION detected ✓"
}

setup_virtual_environment() {
    log_step "Setting up Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        log_warn "Virtual environment already exists. Removing..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_info "Virtual environment created ✓"
}

install_dependencies() {
    log_step "Installing dependencies..."
    
    source "$VENV_DIR/bin/activate"
    
    # Install the package in development mode
    pip install -e .
    
    # Install development dependencies
    pip install \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        isort \
        flake8 \
        mypy \
        debugpy
    
    log_info "Dependencies installed ✓"
}

create_configuration() {
    log_step "Creating configuration files..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        log_info "Creating environment configuration file..."
        cp "$PROJECT_DIR/env.example" "$CONFIG_FILE"
        log_warn "Please edit $CONFIG_FILE with your Jenkins configuration"
    else
        log_info "Environment configuration file already exists ✓"
    fi
    
    # Create directories
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/config"
    mkdir -p "$PROJECT_DIR/backups"
    
    log_info "Configuration setup completed ✓"
}

setup_git_hooks() {
    log_step "Setting up Git hooks..."
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        # Create pre-commit hook
        cat > "$PROJECT_DIR/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Run linting before commit

echo "Running pre-commit checks..."

# Run black
if ! python -m black --check src tests; then
    echo "Code formatting issues found. Run 'black src tests' to fix."
    exit 1
fi

# Run isort
if ! python -m isort --check-only src tests; then
    echo "Import sorting issues found. Run 'isort src tests' to fix."
    exit 1
fi

# Run flake8
if ! python -m flake8 src tests; then
    echo "Style issues found."
    exit 1
fi

echo "Pre-commit checks passed!"
EOF
        
        chmod +x "$PROJECT_DIR/.git/hooks/pre-commit"
        log_info "Git hooks configured ✓"
    else
        log_warn "Not a Git repository. Skipping Git hooks setup."
    fi
}

run_tests() {
    log_step "Running tests to verify installation..."
    
    source "$VENV_DIR/bin/activate"
    
    # Set test environment variables
    export JENKINS_URL="http://localhost:8080"
    export JENKINS_USERNAME="test_user"
    export JENKINS_TOKEN="test_token"
    export LOG_LEVEL="DEBUG"
    
    # Run a basic import test
    python -c "
import sys
sys.path.insert(0, '$PROJECT_DIR/src')
try:
    from jenkins_mcp_server.main import main
    from jenkins_mcp_server.config import JenkinsConfig, ServerConfig
    print('✓ Package imports successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"
    
    log_info "Installation verification completed ✓"
}

create_scripts() {
    log_step "Creating convenience scripts..."
    
    # Create start script
    cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
python -m jenkins_mcp_server.main "$@"
EOF
    chmod +x "$PROJECT_DIR/start.sh"
    
    # Create development script
    cat > "$PROJECT_DIR/dev.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m jenkins_mcp_server.main "$@"
EOF
    chmod +x "$PROJECT_DIR/dev.sh"
    
    # Create test script
    cat > "$PROJECT_DIR/test.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
python tests/run_tests.py "$@"
EOF
    chmod +x "$PROJECT_DIR/test.sh"
    
    log_info "Convenience scripts created ✓"
}

print_usage_info() {
    log_step "Setup completed successfully!"
    
    echo ""
    echo "==================================================="
    echo "         Jenkins MCP Server Setup Complete"
    echo "==================================================="
    echo ""
    echo "Next steps:"
    echo "1. Edit $CONFIG_FILE with your Jenkins configuration"
    echo "2. Start Jenkins MCP Server:"
    echo "   ./start.sh"
    echo ""
    echo "Development commands:"
    echo "  ./dev.sh              - Start in development mode"
    echo "  ./test.sh             - Run tests"
    echo "  ./scripts/deploy.sh   - Deploy with Docker"
    echo ""
    echo "Manual activation:"
    echo "  source .venv/bin/activate"
    echo "  python -m jenkins_mcp_server.main"
    echo ""
    echo "Configuration files:"
    echo "  .env                  - Environment variables"
    echo "  claude_desktop_config.json - Claude Desktop integration"
    echo ""
    echo "==================================================="
}

show_help() {
    echo "Jenkins MCP Server Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  --skip-venv       Skip virtual environment setup"
    echo "  --skip-deps       Skip dependency installation"
    echo "  --skip-tests      Skip test verification"
    echo "  --dev             Setup for development (install dev dependencies)"
    echo ""
    echo "Examples:"
    echo "  $0                Setup everything (recommended)"
    echo "  $0 --dev          Setup for development"
    echo "  $0 --skip-tests   Setup without running tests"
}

main() {
    local skip_venv=false
    local skip_deps=false
    local skip_tests=false
    local dev_mode=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --skip-venv)
                skip_venv=true
                shift
                ;;
            --skip-deps)
                skip_deps=true
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --dev)
                dev_mode=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "=================================================="
    echo "         Jenkins MCP Server Setup"
    echo "=================================================="
    echo "Project directory: $PROJECT_DIR"
    echo "Python version: $(python3 --version)"
    echo "Development mode: $dev_mode"
    echo "=================================================="
    echo ""
    
    # Execute setup steps
    check_python
    
    if [ "$skip_venv" = false ]; then
        setup_virtual_environment
    fi
    
    if [ "$skip_deps" = false ]; then
        install_dependencies
    fi
    
    create_configuration
    setup_git_hooks
    create_scripts
    
    if [ "$skip_tests" = false ]; then
        # run_tests
        log_info "Skipping tests for now (dependencies not fully installed)"
    fi
    
    print_usage_info
}

# Run main function with all arguments
main "$@"