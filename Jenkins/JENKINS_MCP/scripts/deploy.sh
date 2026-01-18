#!/bin/bash

# Jenkins MCP Server Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"

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

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    log_info "System requirements satisfied"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Create environment file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log_warn "Environment file not found. Creating from template..."
        cp env.example "$ENV_FILE"
        log_warn "Please edit $ENV_FILE with your Jenkins configuration before running again."
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p logs config "$BACKUP_DIR"
    
    log_info "Environment setup completed"
}

deploy_services() {
    log_info "Deploying Jenkins MCP Server..."
    
    # Build and start services
    docker compose -f "$COMPOSE_FILE" build
    docker compose -f "$COMPOSE_FILE" up -d
    
    log_info "Services started. Waiting for health checks..."
    
    # Wait for services to be healthy
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose -f "$COMPOSE_FILE" ps --format json | jq -r '.Health' | grep -q "healthy"; then
            log_info "All services are healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy within timeout"
            docker compose -f "$COMPOSE_FILE" logs
            exit 1
        fi
        
        log_info "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check Jenkins
    if curl -s http://localhost:8080/api/json &> /dev/null; then
        log_info "✓ Jenkins is accessible"
    else
        log_error "✗ Jenkins is not accessible"
        exit 1
    fi
    
    # Check MCP Server
    if curl -s http://localhost:8000/health &> /dev/null; then
        log_info "✓ Jenkins MCP Server is accessible"
    else
        log_error "✗ Jenkins MCP Server is not accessible"
        exit 1
    fi
    
    log_info "Deployment verification completed successfully"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  -f, --force       Force deployment without confirmation"
    echo "  -q, --quiet       Quiet mode (minimal output)"
    echo "  --dev             Deploy in development mode"
    echo "  --prod            Deploy in production mode"
    echo ""
    echo "Examples:"
    echo "  $0                Deploy with default settings"
    echo "  $0 --force        Deploy without confirmation prompts"
    echo "  $0 --dev          Deploy in development mode"
}

main() {
    local force_deploy=false
    local quiet_mode=false
    local environment="default"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -f|--force)
                force_deploy=true
                shift
                ;;
            -q|--quiet)
                quiet_mode=true
                shift
                ;;
            --dev)
                environment="development"
                COMPOSE_FILE="docker-compose.dev.yml"
                shift
                ;;
            --prod)
                environment="production"
                COMPOSE_FILE="docker-compose.prod.yml"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    if [ "$quiet_mode" = false ]; then
        echo "================================================"
        echo "         Jenkins MCP Server Deployment"
        echo "================================================"
        echo "Environment: $environment"
        echo "Compose file: $COMPOSE_FILE"
        echo "================================================"
    fi
    
    # Confirmation prompt (unless force flag is used)
    if [ "$force_deploy" = false ]; then
        read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Execute deployment steps
    check_requirements
    setup_environment
    deploy_services
    verify_deployment
    
    if [ "$quiet_mode" = false ]; then
        echo ""
        echo "================================================"
        echo "         Deployment Completed Successfully!"
        echo "================================================"
        echo "Jenkins URL: http://localhost:8080"
        echo "MCP Server URL: http://localhost:8000"
        echo ""
        echo "To view logs: docker compose logs -f"
        echo "To stop services: docker compose down"
        echo "================================================"
    fi
}

# Run main function with all arguments
main "$@"