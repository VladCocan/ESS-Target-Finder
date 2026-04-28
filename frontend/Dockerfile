FROM nginx:alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/nearby.html /usr/share/nginx/html/nearby.html
COPY frontend/saved.html /usr/share/nginx/html/saved.html
COPY frontend/app.js /usr/share/nginx/html/app.js
COPY frontend/nearby.js /usr/share/nginx/html/nearby.js
COPY frontend/js /usr/share/nginx/html/js
COPY frontend/style.css /usr/share/nginx/html/style.css
COPY frontend/brand/css/tokens.css /usr/share/nginx/html/css/tokens.css
COPY frontend/brand/svg /usr/share/nginx/html/svg
COPY frontend/brand/favicons /usr/share/nginx/html/favicons

EXPOSE 80

