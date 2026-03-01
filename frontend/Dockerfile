# build stage
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# if you have custom default.conf, copy it here; else default nginx works for static files
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
