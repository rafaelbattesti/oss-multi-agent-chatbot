# syntax=docker/dockerfile:1

ARG NODE_VERSION=24.13.0-slim

FROM node:${NODE_VERSION} AS deps
WORKDIR /app

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,id=chat-ui-pnpm,target=/pnpm/store pnpm install --frozen-lockfile

FROM node:${NODE_VERSION} AS builder
WORKDIR /app

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV NODE_ENV=production

ARG NEXT_PUBLIC_A2A_SERVER_URL=http://localhost:9999
ENV NEXT_PUBLIC_A2A_SERVER_URL=$NEXT_PUBLIC_A2A_SERVER_URL

RUN corepack enable

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:${NODE_VERSION} AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN mkdir .next && chown node:node .next

COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

CMD ["node", "server.js"]
