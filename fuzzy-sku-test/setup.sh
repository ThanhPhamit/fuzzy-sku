#!/bin/bash

echo "🚀 Setting up Fuzzy SKU OpenSearch Test Environment"
echo "=================================================="

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ Pipenv not found. Installing pipenv..."
    pip install pipenv
fi

# Install dependencies
echo "📦 Installing Python dependencies with pipenv..."
pipenv install

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔧 To run the project:"
echo "  1. Activate the virtual environment: pipenv shell"
echo "  2. Run the test script: python opensearch_test.py"
echo ""
echo "🔗 Or run directly with: pipenv run python opensearch_test.py"
echo ""
echo "📋 Make sure your AWS profile 'welfan-lg-mfa' is configured with:"
echo "  - aws configure --profile welfan-lg-mfa"
echo "  - Your IP address (115.78.131.125) is whitelisted in OpenSearch policy"