FROM aura-backend:production

# Copy seeder code
COPY . /seeder

WORKDIR /seeder

RUN chmod +x /seeder/entrypoint.sh

ENTRYPOINT ["/seeder/entrypoint.sh"]
