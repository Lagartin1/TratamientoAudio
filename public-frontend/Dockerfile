FROM node:20-alpine AS build

WORKDIR /app

ARG NG_APP_API_URL
ENV NG_APP_API_URL=$NG_APP_API_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build -- --configuration development

FROM nginx:1.27-alpine

COPY --from=build /app/dist/public-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
