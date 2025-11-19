FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install || true
COPY frontend ./frontend
WORKDIR /app/frontend
EXPOSE 3023
ENV PORT=3023
CMD ["npx", "serve", ".", "-l", "3023"]
