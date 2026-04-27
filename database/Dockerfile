FROM pgvector/pgvector:pg15

# Copy init scripts so they run automatically on first container startup
COPY docker-init/init.sql /docker-entrypoint-initdb.d/init.sql
