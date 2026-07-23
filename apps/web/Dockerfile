# Local development image (next dev with hot reload via bind mount). Not a production
# build — revisit under a dedicated deployment task (standalone output, non-root user, etc).
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
