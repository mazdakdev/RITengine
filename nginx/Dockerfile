
FROM nginx:alpine

RUN apk add --no-cache gettext

COPY default.conf.template /etc/nginx/templates/

# build  NGINX's default.conf using .env values
CMD /bin/sh -c "envsubst '\$FRONTEND_URL \$BACKEND_URL' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"