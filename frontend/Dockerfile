FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/vite.config.js frontend/index.html ./
COPY frontend/src ./src
COPY frontend/brand ./brand
RUN npm install && npm run build

FROM nginx:alpine AS runtime
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/brand/favicons /usr/share/nginx/html/brand/favicons
COPY frontend/brand/svg /usr/share/nginx/html/brand/svg

EXPOSE 80

