#!/bin/bash
# Pre-build script to ensure clean builds on Render
# Prevents stale cache issues that have plagued us multiple times

echo "🧹 Cleaning Next.js cache..."

# Remove .next cache directory
rm -rf .next

# Remove node_modules/.cache (Webpack cache)
rm -rf node_modules/.cache

# Log git commit for debugging
if [ -n "$RENDER_GIT_COMMIT" ]; then
  echo "📦 Building commit: $RENDER_GIT_COMMIT"
fi

echo "✅ Pre-build cleanup complete"
