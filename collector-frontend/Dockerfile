FROM node:20-alpine AS build

WORKDIR /app

ARG NG_APP_URL_COLLECTOR_API
ARG COLLECTOR_FRONTEND_BASE_HREF=/
ENV NG_APP_URL_COLLECTOR_API=$NG_APP_URL_COLLECTOR_API

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build -- --configuration development --base-href $COLLECTOR_FRONTEND_BASE_HREF

FROM nginx:1.27-alpine

COPY --from=build /app/dist/collector-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
