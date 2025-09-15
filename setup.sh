#!/bin/bash

echo "🚀 Setting up Repair DIY AI Monorepo..."

# Install pnpm if not already installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd apps/frontend
pnpm install
cd ../..

# Setup backend Python environment
echo "🐍 Setting up backend Python environment..."
cd apps/backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "⚠️  Please edit apps/backend/.env and add your OpenAI API key"
fi

cd ../..

echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  Frontend: pnpm dev:frontend"
echo "  Backend:  pnpm dev:backend"
echo "  Both:     pnpm dev"
echo ""
echo "Don't forget to add your OpenAI API key to apps/backend/.env"
