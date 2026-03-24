FROM node:22-alpine AS build

WORKDIR /app

COPY app/frontend/package*.json ./
RUN npm install

COPY app/frontend/ ./frontend
COPY app/languages ./languages
WORKDIR /app/frontend
RUN npm run build

FROM nginx:stable-alpine

RUN rm -rf /usr/share/nginx/html/*

COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY app/frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]