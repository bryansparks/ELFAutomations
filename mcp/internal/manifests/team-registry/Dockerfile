FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY mcp-servers-ts/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source files
COPY mcp-servers-ts/src ./src
COPY mcp-servers-ts/tsconfig.json ./

# Install TypeScript and build
RUN npm install -D typescript @types/node
RUN npx tsc

# Run the server
CMD ["node", "dist/team-registry/server.js"]
