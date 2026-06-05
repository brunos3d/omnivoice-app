# ADR-0005: Edition-scoped model availability (licensing-governed)

- **Status:** Accepted
- **Date:** 2026-06-04
- **Deciders:** Bruno Silva (product owner), architecture planning

## Context

PeakVox is model-agnostic ([ADR-0004](adr-0004-voice-variant-model-separation.md)), but **not every
model may legally run in every edition**. Model availability is governed by **licensing**, and
Community Edition (CE) and Cloud are separate deployment targets:

- **CE** (self-hosted infrastructure layer) may run a broad set: OmniVoice, OmniVoice Singing,
  Fish Audio, Kokoro, OpenVoice, Chatterbox, future community models.
- **Cloud** (managed ecosystem layer) may run a *different* set: OmniVoice, PeakVox-native
  models, commercially-licensed providers.

Some models may be **CE-only and never available in Cloud** — e.g. Fish Audio requires a
commercial-licensing review and (for now) may only be distributed/executed in self-hosted CE.

Therefore the Runtime must **not assume that every installed model is available in the current
edition.** Availability must be controlled through declared metadata, not code branching.

## Options considered

1. **Assume all installed models are available everywhere.** Simplest, but legally unsafe — a
   CE-only model could be exposed/executed in Cloud. Rejected.

2. **Edition-scoped availability declared on the Model, enforced by the Runtime.** Each model
   declares the editions it may run in (the existing `editions` field) plus licensing metadata;
   the registry filters and the Runtime refuses to resolve a model not available in the active
   edition. **Chosen.**

3. **Fork the catalog per edition.** A separate CE vs Cloud model catalog. Violates the
   one-schema/one-codebase principle and duplicates definitions. Rejected.

## Decision

**Model availability is edition-scoped and declared, never inferred.** The mechanism:

- **`Model.editions`** (existing JSON list, e.g. `["community"]`, `["community","cloud"]`) is the
  authoritative availability declaration. A model is *available* in edition `E` iff `E ∈
  editions`.
- **`ModelLicense`** ([ADR-0002](adr-0002-model-as-first-class-entity.md)) records the licensing
  basis (`code`, `commercial_use`, `url`) that *justifies* the `editions` value. Licensing is
  documentation + policy input; `editions` is the enforcement field.
- **The Model Registry** filters catalog listings by edition (`list_models(edition)` — already
  implemented).
- **The PeakVox Runtime enforces availability**: resolving/generating a model that is not
  available in `settings.EDITION` raises `ModelNotAvailableInEdition` (mapped to HTTP 409). The
  Runtime never branches on a model id/name — it reads the declared `editions`.

CE remains the broad infrastructure layer; Cloud is a curated subset. The same codebase + schema
serve both; only the declared `editions` differ.

## Consequences

- **Positive:** licensing is respected structurally; CE can ship models (e.g. Fish Audio) that
  Cloud must not run, with zero forked schema/catalog; the Runtime stays model-agnostic
  (availability is data); adding/retiring a model from an edition is a metadata change.
- **Negative / costs:** every model must declare correct `editions`; an availability check is
  added to the resolution/generation path; operators must keep `editions` aligned with legal
  review.
- **Follow-ups:** the Runtime availability check + `ModelNotAvailableInEdition` (Phase 3.8); the
  Fish Audio adapter ships `editions=["community"]`; the marketplace/Cloud surfaces filter by
  edition availability ([Product §3](../ARCHITECTURE/product-architecture.md)). Ties to
  [ADR-0003](adr-0003-model-capability-contract.md) (capabilities) — availability and capability are
  orthogonal: a model can be capable yet unavailable in an edition.
