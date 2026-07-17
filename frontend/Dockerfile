# Stage 1: Build ứng dụng React bằng Node.js (Giữ nguyên của bạn)
FROM node:20-alpine AS build-stage

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Stage 2: Sử dụng Nginx để vận hành Production Build nhằm tối ưu hiệu năng
FROM nginx:alpine

# Sao chép file cấu hình Nginx tùy chỉnh để hỗ trợ Single Page Application (SPA) Routing
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Ghi đè cấu hình default của Nginx để kích hoạt try_files phục vụ React Router
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]