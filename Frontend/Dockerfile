# Use Node LTS image
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files first (for caching)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run dev server with host flag so Docker can access it
CMD ["npm", "run", "dev", "--", "--host"]
