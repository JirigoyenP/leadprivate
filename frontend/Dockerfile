FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Railway uses dynamic PORT
ENV PORT=80
ENV BACKEND_URL=http://localhost:8000

EXPOSE 80

# nginx:alpine image automatically processes templates in /etc/nginx/templates/
CMD ["nginx", "-g", "daemon off;"]
