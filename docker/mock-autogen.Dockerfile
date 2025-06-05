FROM node:18-alpine

WORKDIR /app

# Copy the mock autogen server
COPY docker/mock-autogen-server.js server.js

EXPOSE 8081
CMD ["node", "server.js"]
