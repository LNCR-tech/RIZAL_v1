# Use official Node.js image
FROM node:20

# Set working directory inside the container
WORKDIR /app

# Note: we intentionally do NOT run `npm install` during image build.
# On Docker Desktop/WSL2 + BuildKit, the esbuild postinstall can intermittently fail
# with ETXTBSY ("text file busy"). Dependencies are installed at container startup
# into the `/app/node_modules` volume by `scripts/dev-entrypoint.sh`.
COPY package.json package-lock.json ./
COPY scripts ./scripts

# Expose the port used by Vite dev server
EXPOSE 5173

# Start Vite dev server
CMD ["sh", "/app/scripts/dev-entrypoint.sh"]
