#!/bin/bash

# Update package index
sudo apt-get update

# Install required dependencies for Node.js
sudo apt-get install -y ca-certificates curl gnupg

# Create directory for apt keyrings
sudo mkdir -p /etc/apt/keyrings

# Add NodeSource signing key
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

# Add Node.js repository
NODE_MAJOR=20 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list

# Update package index again
sudo apt-get update

# Install Node.js
sudo apt-get install -y nodejs

# Verify installation
node -v
npm -v

# Install tweet-harvest globally
sudo npm install -g tweet-harvest@2.6.0
