FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S seekora && adduser -S seekora -G seekora
COPY --from=builder /app/public ./public
COPY --from=builder --chown=seekora:seekora /app/.next/standalone ./
COPY --from=builder --chown=seekora:seekora /app/.next/static ./.next/static
USER seekora
EXPOSE 3000
CMD ["node", "server.js"]
