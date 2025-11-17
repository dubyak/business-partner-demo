#!/bin/bash

# =====================================================
# Supabase Automated Setup Script
# =====================================================
# This script automates the entire Supabase setup process
# =====================================================

set -e  # Exit on any error

echo "🚀 Business Partner AI - Supabase Setup"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# =====================================================
# Step 1: Check if Supabase CLI is installed
# =====================================================
echo -e "${BLUE}Step 1: Checking for Supabase CLI...${NC}"

if ! command -v supabase &> /dev/null; then
    echo -e "${YELLOW}Supabase CLI not found. Installing...${NC}"
    
    # Check OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install supabase/tap/supabase
        else
            echo "Installing via npm..."
            npm install -g supabase
        fi
    else
        # Linux or other
        echo "Installing via npm..."
        npm install -g supabase
    fi
    
    echo -e "${GREEN}✓ Supabase CLI installed${NC}"
else
    echo -e "${GREEN}✓ Supabase CLI already installed ($(supabase --version))${NC}"
fi

echo ""

# =====================================================
# Step 2: Login to Supabase
# =====================================================
echo -e "${BLUE}Step 2: Authenticating with Supabase...${NC}"

if supabase projects list &> /dev/null; then
    echo -e "${GREEN}✓ Already logged in${NC}"
else
    echo "Opening browser for authentication..."
    supabase login
    echo -e "${GREEN}✓ Successfully logged in${NC}"
fi

echo ""

# =====================================================
# Step 3: Choose to create or link project
# =====================================================
echo -e "${BLUE}Step 3: Project Setup${NC}"
echo "Do you want to:"
echo "  1) Create a new Supabase project"
echo "  2) Link to an existing project"
echo "  3) Skip (already configured)"
read -p "Enter choice (1, 2, or 3): " project_choice

if [ "$project_choice" = "1" ]; then
    echo ""
    echo "Creating new Supabase project..."
    echo ""
    
    # Get organization ID
    echo "Available organizations:"
    supabase orgs list
    echo ""
    read -p "Enter your organization ID: " org_id
    
    # Get project name
    read -p "Enter project name (default: business-partner-ai): " project_name
    project_name=${project_name:-business-partner-ai}
    
    # Get region
    echo ""
    echo "Common regions:"
    echo "  - us-east-1 (N. Virginia)"
    echo "  - us-west-1 (N. California)"
    echo "  - eu-west-1 (Ireland)"
    echo "  - ap-southeast-1 (Singapore)"
    read -p "Enter region (default: us-east-1): " region
    region=${region:-us-east-1}
    
    # Create project
    echo ""
    echo "Creating project '$project_name' in region '$region'..."
    supabase projects create "$project_name" --org-id "$org_id" --region "$region"
    
    echo -e "${GREEN}✓ Project created${NC}"
    echo ""
    echo "Waiting for project to be ready (this takes 2-3 minutes)..."
    sleep 30
    
elif [ "$project_choice" = "2" ]; then
    echo ""
    echo "Available projects:"
    supabase projects list
    echo ""
    read -p "Enter your project reference ID: " project_ref
    
    echo "Linking to project..."
    supabase link --project-ref "$project_ref"
    
    echo -e "${GREEN}✓ Project linked${NC}"
    
elif [ "$project_choice" = "3" ]; then
    echo -e "${YELLOW}Skipping project setup${NC}"
else
    echo -e "${RED}Invalid choice. Exiting.${NC}"
    exit 1
fi

echo ""

# =====================================================
# Step 4: Push database migrations
# =====================================================
echo -e "${BLUE}Step 4: Applying database migrations...${NC}"

# Check if migrations exist
if [ ! -d "supabase/migrations" ]; then
    echo -e "${RED}Error: supabase/migrations directory not found${NC}"
    exit 1
fi

echo "Pushing database schema to remote..."
supabase db push

echo -e "${GREEN}✓ Database schema applied${NC}"
echo ""

# =====================================================
# Step 5: Verify setup
# =====================================================
echo -e "${BLUE}Step 5: Verifying setup...${NC}"

# Get project info
echo "Fetching project credentials..."
PROJECT_REF=$(cat .git/config 2>/dev/null | grep 'project-ref' | cut -d '=' -f2 | tr -d ' ' || echo "")

if [ -z "$PROJECT_REF" ]; then
    echo -e "${YELLOW}Could not auto-detect project ref. You'll need to get credentials manually.${NC}"
else
    echo ""
    echo -e "${GREEN}Project credentials:${NC}"
    supabase projects api-keys --project-ref "$PROJECT_REF" 2>/dev/null || echo "Run: supabase projects api-keys --project-ref YOUR_PROJECT_REF"
fi

echo ""
echo -e "${GREEN}✓ Setup verification complete${NC}"
echo ""

# =====================================================
# Step 6: Generate environment variables
# =====================================================
echo -e "${BLUE}Step 6: Generating environment variables...${NC}"

if [ -z "$PROJECT_REF" ]; then
    echo "Please run this command to get your credentials:"
    echo "  supabase projects api-keys --project-ref YOUR_PROJECT_REF"
else
    echo "Add these to your .env files:"
    echo ""
    echo "SUPABASE_URL=https://$PROJECT_REF.supabase.co"
    echo "SUPABASE_ANON_KEY=<get from: supabase projects api-keys --project-ref $PROJECT_REF>"
    echo "SUPABASE_SERVICE_ROLE_KEY=<get from: supabase projects api-keys --project-ref $PROJECT_REF>"
fi

echo ""

# =====================================================
# Step 7: Optional - Generate TypeScript types
# =====================================================
echo -e "${BLUE}Step 7: Generate TypeScript types?${NC}"
read -p "Generate TypeScript types for your database? (y/n): " gen_types

if [ "$gen_types" = "y" ] || [ "$gen_types" = "Y" ]; then
    mkdir -p types
    echo "Generating types..."
    supabase gen types typescript --linked > types/supabase.ts
    echo -e "${GREEN}✓ Types generated at types/supabase.ts${NC}"
else
    echo "Skipping type generation"
fi

echo ""

# =====================================================
# Step 8: Install client libraries
# =====================================================
echo -e "${BLUE}Step 8: Install Supabase client libraries?${NC}"
read -p "Install @supabase/supabase-js for Node.js? (y/n): " install_node

if [ "$install_node" = "y" ] || [ "$install_node" = "Y" ]; then
    if [ -d "backend" ]; then
        echo "Installing in backend/..."
        (cd backend && npm install @supabase/supabase-js)
        echo -e "${GREEN}✓ Installed in backend/${NC}"
    fi
fi

echo ""

read -p "Install supabase for Python? (y/n): " install_python

if [ "$install_python" = "y" ] || [ "$install_python" = "Y" ]; then
    if [ -d "python-backend" ]; then
        echo "Installing in python-backend/..."
        (cd python-backend && pip install supabase)
        echo -e "${GREEN}✓ Installed in python-backend/${NC}"
    fi
fi

echo ""

# =====================================================
# Setup Complete
# =====================================================
echo "=========================================="
echo -e "${GREEN}✨ Supabase Setup Complete! ✨${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Add Supabase credentials to your .env files"
echo "  2. Initialize Supabase client in your backend code"
echo "  3. Add authentication to your frontend"
echo "  4. Test the setup with a sample user"
echo ""
echo "Useful commands:"
echo "  supabase status          - Check local Supabase status"
echo "  supabase start           - Start local development"
echo "  supabase db push         - Push new migrations"
echo "  supabase db pull         - Pull remote schema changes"
echo "  supabase projects list   - List your projects"
echo ""
echo "Documentation:"
echo "  - See SUPABASE_CLI_SETUP.md for detailed instructions"
echo "  - See SUPABASE_QUICK_REFERENCE.md for quick commands"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

