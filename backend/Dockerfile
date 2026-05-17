FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM node:20-alpine AS backend

WORKDIR /app/backend

ENV NODE_ENV=production
ENV PORT=5000

COPY backend/package*.json ./
RUN npm ci --omit=dev

COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./public

EXPOSE 5000

CMD ["npm", "start"]