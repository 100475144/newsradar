
ARG NODE_VERSION=trixie

# Use a lightweight Node.js image for development
FROM node:${NODE_VERSION} AS dev

# Set the working directory inside the container
WORKDIR /code

# Copy package-related files first to leverage Docker's caching mechanism
COPY package.json package-lock.json* .

# Install project dependencies
RUN --mount=type=cache,target=/root/.npm npm install

# Container entrypoint 
CMD ["npm", "run", "dev"]