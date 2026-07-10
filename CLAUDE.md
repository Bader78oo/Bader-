# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

This repo is based on [nextjs/saas-starter](https://github.com/nextjs/saas-starter): a Next.js SaaS
template with email/password auth, Stripe subscriptions, and a team-based dashboard. It's intended
as the base to build a real product on top of, not a finished app.

## Commands

Package manager is pnpm (there's a `pnpm-lock.yaml`; no other lockfile should be added).

```bash
pnpm install          # install deps
pnpm dev              # start dev server (Next.js + Turbopack) at localhost:3000
pnpm build            # production build
pnpm start            # run the production build

pnpm db:setup         # interactive wizard that writes .env (Postgres URL, Stripe keys, AUTH_SECRET)
pnpm db:migrate       # apply Drizzle migrations
pnpm db:seed          # seed a default team + user (test@test.com / admin123)
pnpm db:generate      # generate a new Drizzle migration from schema.ts changes
pnpm db:studio        # open Drizzle Studio to browse the DB
```

There is no test suite, linter, or typecheck script configured in `package.json` — `tsc --noEmit`
is possible for a manual type check but is not wired up as a script.

Local Stripe webhooks (needed for subscription flows to work in dev):
```bash
stripe login
stripe listen --forward-to localhost:3000/api/stripe/webhook
```
Test card for Checkout: `4242 4242 4242 4242`, any future expiry, any 3-digit CVC.

## Architecture

**Routing** uses the Next.js App Router with two route groups in `app/`:
- `app/(login)/` — `/sign-in`, `/sign-up`, and `actions.ts` (Server Actions for auth)
- `app/(dashboard)/` — marketing page (`/`), `/pricing`, and `/dashboard/*` (activity, general
  settings, security), all gated by auth
- `app/api/` — route handlers: Stripe checkout redirect + webhook, and JSON endpoints for
  team/user

**Auth** (`lib/auth/`): stateless sessions, not DB-backed. `session.ts` signs a JWT (`jose`,
HS256, keyed by `AUTH_SECRET`) containing just `{ user: { id } }` and stores it in an `httpOnly`
`session` cookie. `middleware.ts` (root) runs on every non-API request: it redirects
unauthenticated users away from `/dashboard/*`, and on every `GET` transparently re-signs and
re-issues the cookie to slide the 1-day expiry forward. Passwords are hashed with `bcryptjs`.
`lib/auth/middleware.ts` provides `validatedAction`, `validatedActionWithUser`, and `withTeam` —
wrappers used to compose Zod validation + auth/team-loading around Server Actions instead of
repeating that boilerplate in every action.

**Data layer** (`lib/db/`): Postgres via `postgres` + Drizzle ORM. `schema.ts` defines `users`,
`teams`, `teamMembers`, `invitations`, `activityLogs` — note that **team**, not user, is the
billing entity: Stripe customer/subscription/product/plan fields live on `teams`, and every user
belongs to a team via `teamMembers` with a per-team `role` (Owner/Member RBAC). `queries.ts`
centralizes all reads (`getUser`, `getTeamForUser`, `getTeamByStripeCustomerId`, etc.) — call
these rather than writing ad hoc Drizzle queries in routes/actions. `activityLogs` is written to
on auth/team events (see `ActivityType` enum in `schema.ts`); when adding a new mutable action,
log it the same way. Schema changes: edit `schema.ts`, run `pnpm db:generate`, then
`pnpm db:migrate`.

**Payments** (`lib/payments/stripe.ts`): all Stripe SDK calls are isolated here —
`createCheckoutSession`, `createCustomerPortalSession`, `handleSubscriptionChange` (called from
the webhook route to sync subscription status onto the owning `team` row), and
`getStripePrices`/`getStripeProducts` (used by the pricing page, so Stripe's dashboard is the
source of truth for plans/prices, not code).

**UI**: Tailwind CSS v4 + shadcn/ui primitives in `components/ui/` (Radix-based). Path alias `@/*`
maps to the repo root (see `tsconfig.json`), e.g. `@/lib/db/schema`.

## Environment

`.env` (not `.env.local`) holds `POSTGRES_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`BASE_URL`, `AUTH_SECRET` — see `.env.example`. `pnpm db:setup` generates this interactively
rather than it being hand-edited from scratch.
