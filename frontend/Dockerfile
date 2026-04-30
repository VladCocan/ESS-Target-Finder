FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json vite.config.js index.html ./
COPY src ./src
COPY brand ./brand
RUN npm ci && npm run build

FROM nginx:alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY brand/favicons /usr/share/nginx/html/brand/favicons
COPY brand/svg /usr/share/nginx/html/brand/svg

EXPOSE 80

