# Build context is the assignment root (see docker-compose.yml), so every COPY
# path below is relative to FDE/Assignment_1_Live_Translate/.
#
# Alpine over slim: a smaller base for the same result, verified to build on
# linux/amd64 without compiling anything. No native-module risk here — express,
# cors and dotenv are pure JS, so there is nothing for musl to break. Re-check
# if a dependency with a .node binding is added.
FROM node:22-alpine

# server.js resolves the widget with path.join(__dirname, "..", "..", "widget"),
# so the image has to mirror the repo layout: the app two levels below the
# directory that holds widget/. Flattening this into /app would make that climb
# resolve to /widget and /widget.js would 500 at runtime.
WORKDIR /app/backend/gateway-node

# Manifest before source, so the install layer is cached and only re-runs when
# the dependencies actually change.
COPY backend/gateway-node/package.json backend/gateway-node/package-lock.json ./
RUN npm ci --omit=dev

COPY backend/gateway-node/ ./
COPY widget/ /app/widget/

# Express checks NODE_ENV: production turns off verbose error output and stops
# it from leaking stack traces to the browser.
ENV NODE_ENV=production

# The node images ship a non-root "node" user (uid 1000). The gateway only
# reads its files and logs to stdout, so it needs no ownership changes.
USER node

EXPOSE 8787

CMD ["node", "server.js"]
