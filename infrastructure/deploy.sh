#!/bin/bash

# Japanese SKU Search Infrastructure Deployment Script
# Usage: ./deploy.sh [staging|production]

set -e

# Configuration
ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${SCRIPT_DIR}/environments/${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    log_error "Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

if [[ ! -d "$ENV_DIR" ]]; then
    log_error "Environment directory not found: $ENV_DIR"
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed or not in PATH"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed or not in PATH"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Initialize Terraform
terraform_init() {
    log_info "Initializing Terraform for $ENVIRONMENT environment..."
    cd "$ENV_DIR"
    terraform init
    log_success "Terraform initialized"
}

# Plan deployment
terraform_plan() {
    log_info "Planning Terraform deployment..."
    cd "$ENV_DIR"
    terraform plan -out="terraform.plan"
    log_success "Terraform plan completed"
}

# Apply deployment
terraform_apply() {
    log_info "Applying Terraform deployment..."
    cd "$ENV_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_warning "You are about to deploy to PRODUCTION environment!"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    terraform apply "terraform.plan"
    log_success "Terraform deployment completed"
}

# Show outputs
show_outputs() {
    log_info "Deployment outputs:"
    cd "$ENV_DIR"
    terraform output
}

# Main execution
main() {
    log_info "Starting deployment for $ENVIRONMENT environment"
    
    check_prerequisites
    terraform_init
    terraform_plan
    terraform_apply
    show_outputs
    
    log_success "Deployment completed successfully!"
    log_info "API Gateway URL: $(cd "$ENV_DIR" && terraform output -raw api_gateway_url)"
    log_info "Search Endpoint: $(cd "$ENV_DIR" && terraform output -raw search_endpoint_url)"
    log_info "Cognito Login URL: $(cd "$ENV_DIR" && terraform output -raw cognito_login_url)"
}

# Cleanup function
cleanup() {
    if [[ -f "$ENV_DIR/terraform.plan" ]]; then
        rm "$ENV_DIR/terraform.plan"
        log_info "Cleaned up temporary files"
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Execute main function
main