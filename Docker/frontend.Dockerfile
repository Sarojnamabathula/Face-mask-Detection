# --- Frontend Dockerfile ---
# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Build the frontend
COPY frontend/ ./
RUN npm run build

# Production stage
FROM nginx:alpine as production-stage

# Copy the built assets to Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY Docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
