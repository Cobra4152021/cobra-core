import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildCorrelationId,
  formatBugNumber,
  parseBugNumber,
  redactString,
  redactValue,
  hashPayload,
  triageEvent,
  canTransitionFeedback,
  buildReplayToken,
  SENTINEL_DOMAIN,
} from "../src/sentinel/index.js";

describe("KC-012 Sentinel", () => {
  it("builds correlation and bug ids", () => {
    const corr = buildCorrelationId({
      requestId: "req_abcdef0123456789",
      sessionId: "ses_hello",
      investigationId: "inv_world",
    });
    assert.match(corr, /^corr_/);
    assert.equal(formatBugNumber(2026, 42), "BUG-2026-000042");
    assert.deepEqual(parseBugNumber("BUG-2026-000042"), { year: 2026, seq: 42 });
  });

  it("redacts secrets and never keeps evidence bodies by key", () => {
    const s = redactString("Authorization: Bearer abc.def.ghi cookie=hidden_grid_session=sekrit");
    assert.ok(!s.includes("sekrit"));
    assert.ok(s.includes("[REDACTED]"));
    const obj = redactValue(
      { password: "x", token: "y", note: "ok", evidence: "SECRET_DOC" },
      "root",
    ) as Record<string, unknown>;
    assert.equal(obj.password, "[REDACTED]");
    assert.equal(obj.evidence, "[REDACTED]");
    assert.equal(obj.note, "ok");
  });

  it("hashes payloads without retaining content", async () => {
    const h = await hashPayload("document-bytes-not-stored");
    assert.equal(h.length, 64);
    assert.notEqual(h, "document-bytes-not-stored");
  });

  it("triages CSRF/RBAC and never auto-closes", () => {
    const t = triageEvent({ message: "Missing required header X-Hidden-Grid-Auth CSRF" });
    assert.equal(t.domain, "csrf");
    assert.equal(t.autoClose, false);
    assert.ok(t.confidence >= 0.9);
    const r = triageEvent({ message: "Route policy is not configured Forbidden" });
    assert.equal(r.domain, "rbac");
  });

  it("enforces feedback workflow transitions", () => {
    assert.equal(canTransitionFeedback("new", "acknowledged"), true);
    assert.equal(canTransitionFeedback("new", "closed"), false);
    assert.equal(canTransitionFeedback("resolved", "closed"), true);
  });

  it("builds replay tokens with hashes only", () => {
    const tok = buildReplayToken({
      randomHex: "aabbccddeeff001122334455",
      featureFlags: { SENTINEL_ENABLED: true },
      browser: "Chrome",
      route: "/admin/sentinel",
      apiRequestIds: ["req_1"],
      workerVersion: "v1",
      correlationId: "corr_x",
      payloadHashes: ["abc"],
    });
    assert.match(tok.replayId, /^replay_/);
    assert.deepEqual(tok.payloadHashes, ["abc"]);
    assert.equal(SENTINEL_DOMAIN.id, "cobra.sentinel");
  });
});
