# syntax=docker/dockerfile:1

ARG NODE_VERSION=22.15.0

# Base image with Node
FROM node:${NODE_VERSION}-alpine AS base
WORKDIR /usr/src/app

# Install dependencies
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy source and build
COPY . .

RUN npm run build

# Install serve globally to serve the build
RUN npm install -g serve

# Final image (minimal)
FROM node:${NODE_VERSION}-alpine

WORKDIR /usr/src/app

# Copy only the build artifacts and serve
COPY --from=base /usr/src/app/build ./build
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
