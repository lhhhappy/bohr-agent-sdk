#!/bin/bash

OS="$(uname)"
REPO_URL="https://raw.githubusercontent.com/dptech-corp/bohr-agent-sdk/refs/heads/master"

echo "Installing dependencies..."

if [ "$OS" == "Linux" ] || [ "$OS" == "Darwin" ]; then
  python3 -m pip install --upgrade pip
  python3 -m pip install bohr-agent-sdk --upgrade
elif [ "$OS" == "Windows_NT" ] || [[ "$OS" == MINGW* ]] || [[ "$OS" == CYGWIN* ]]; then
  python -m pip install --upgrade pip
  python -m pip install bohr-agent-sdk --upgrade
else
  echo "Unsupported operating system: $OS"
  exit 1
fi

echo "DP Agent CLI installed successfully!"
echo "Use 'dp-agent --help' to see available commands."
