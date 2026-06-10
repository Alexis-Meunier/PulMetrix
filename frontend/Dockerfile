ARG NODE_VERSION=26-alpine3.22

FROM node:${NODE_VERSION} AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install          # ← instead of npm ci
COPY . .
RUN npm run build

FROM nginx:alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]