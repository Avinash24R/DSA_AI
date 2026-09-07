FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY home.html /usr/share/nginx/html/home.html
COPY problem.html /usr/share/nginx/html/problem.html
COPY progress.html /usr/share/nginx/html/progress.html
COPY user.html /usr/share/nginx/html/user.html

COPY style.css /usr/share/nginx/html/style.css
COPY app.js /usr/share/nginx/html/app.js

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80