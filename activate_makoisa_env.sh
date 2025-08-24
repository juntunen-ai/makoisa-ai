#!/bin/bash
# Makoisa AI Environment Activation Script

echo "🚀 Activating Makoisa AI Development Environment"
echo "================================================"

# Deactivate any existing virtual environment
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo "🔄 Deactivating existing virtual environment: $VIRTUAL_ENV"
    deactivate
fi

# Change to the correct directory
cd /Users/harrijuntunen/makoisa-ai

# Verify we're in the right directory
if [ ! -f "recipe_ai/ui/app.py" ]; then
    echo "❌ Error: Not in the correct makoisa-ai directory!"
    echo "Current directory: $(pwd)"
    return 1
fi

# Activate the virtual environment
echo "🔄 Activating makoisa-ai virtual environment..."
source venv/bin/activate

# Confirm we're in the right place
echo "✅ Current directory: $(pwd)"
echo "✅ Python executable: $(which python)"
echo "✅ Virtual environment: $(echo $VIRTUAL_ENV)"

# Add aliases for convenience
alias runui="cd /Users/harrijuntunen/makoisa-ai/recipe-ui && npm run dev"
alias runapi="cd /Users/harrijuntunen/makoisa-ai && source venv/bin/activate && python server_original.py"

echo ""
echo "🎯 Quick commands:"
echo "   runui   - Start React UI development server"
echo "   runapi  - Start FastAPI server"
echo ""
echo "📁 Project structure verified:"
ls -la recipe-ui/package.json

echo ""
echo "🎉 Makoisa AI environment is ready!"
