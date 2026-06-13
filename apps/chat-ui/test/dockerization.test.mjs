import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import test from "node:test";

const appRoot = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(appRoot, "..", "..");

async function readRelative(root, relativePath) {
  return readFile(path.join(root, relativePath), "utf8");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test("Next config enables standalone output", async () => {
  const config = await readRelative(appRoot, "next.config.ts");

  assert.match(config, /output:\s*["']standalone["']/);
});

test("Dockerfile builds and runs the standalone server", async () => {
  const dockerfilePath = path.join(appRoot, "Dockerfile");

  assert.equal(existsSync(dockerfilePath), true);

  const dockerfile = await readFile(dockerfilePath, "utf8");

  assert.match(dockerfile, /FROM\s+node:[^\s]+\s+AS\s+deps/);
  assert.match(dockerfile, /corepack enable/);
  assert.match(dockerfile, /pnpm install --frozen-lockfile/);
  assert.match(dockerfile, /pnpm build/);
  assert.match(dockerfile, /COPY --from=builder .*\/app\/\.next\/standalone \.\//);
  assert.match(dockerfile, /COPY --from=builder .*\/app\/\.next\/static \.\/\.next\/static/);
  assert.match(dockerfile, /ENV PORT=3000/);
  assert.match(dockerfile, /ENV HOSTNAME="0\.0\.0\.0"/);
  assert.match(dockerfile, /EXPOSE 3000/);
  assert.match(dockerfile, /USER node/);
  assert.match(dockerfile, /CMD \["node", "server\.js"\]/);
});

test(".dockerignore removes local-only Docker context inputs", async () => {
  const dockerignorePath = path.join(appRoot, ".dockerignore");

  assert.equal(existsSync(dockerignorePath), true);

  const dockerignore = await readFile(dockerignorePath, "utf8");

  for (const pattern of [
    "node_modules",
    ".next",
    "out",
    ".env",
    ".env*.local",
    ".git",
    ".agents",
    ".claude",
    "*.log",
  ]) {
    assert.match(dockerignore, new RegExp(`(^|\\n)${escapeRegExp(pattern)}(/)?(\\n|$)`));
  }
});

test("root compose file defines the chat-ui service", async () => {
  const composePath = path.join(repoRoot, "docker-compose.yaml");

  assert.equal(existsSync(composePath), true);

  const compose = await readFile(composePath, "utf8");

  assert.match(compose, /services:\s*\n\s+chat-ui:/);
  assert.match(compose, /context:\s+\.\/apps\/chat-ui/);
  assert.match(compose, /dockerfile:\s+Dockerfile/);
  assert.match(compose, /NEXT_PUBLIC_A2A_SERVER_URL:\s+\$\{NEXT_PUBLIC_A2A_SERVER_URL:-http:\/\/localhost:9999\}/);
  assert.match(compose, /PORT:\s+"3000"/);
  assert.match(compose, /HOSTNAME:\s+"0\.0\.0\.0"/);
  assert.match(compose, /"3000:3000"/);
});

test("system docs record the UI as a standalone app container", async () => {
  const system = await readRelative(repoRoot, "docs/SYSTEM.md");

  assert.match(system, /standalone app container/);
  assert.match(system, /built from `apps\/chat-ui`/);
});
