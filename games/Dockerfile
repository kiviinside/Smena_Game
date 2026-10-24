FROM nginx:alpine

COPY smena-1.0-dists/smena-1.0-web/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]