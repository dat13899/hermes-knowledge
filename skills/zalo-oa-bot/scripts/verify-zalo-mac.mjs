#!/usr/bin/env node
/**
 * Verify chữ ký webhook Zalo OA — từ dữ liệu thật.
 *
 * Công thức: mac = sha256(appId + rawBody + timestamp + oaSecretKey)
 * (SHA-256 thường, KHÔNG phải HMAC)
 *
 * Cách dùng:
 *   node verify-zalo-mac.mjs <appId> <rawBody> <timestamp> <oaSecretKey> [signatureHeader]
 *   - signatureHeader: header X-ZEvent-Signature (có thể kèm "mac=" prefix — tự strip)
 *   - Nếu không truyền signatureHeader, chỉ in MAC tính được
 *
 * Exit code: 0 = MATCH, 1 = mismatch, 2 = thiếu tham số
 */
import crypto from "node:crypto";

const [, , appId, rawBody, timestamp, secret, sigHeader] = process.argv;

if (!appId || !rawBody || !timestamp || !secret) {
  console.error("Thiếu tham số. Dùng: node verify-zalo-mac.mjs <appId> <rawBody> <timestamp> <oaSecretKey> [signatureHeader]");
  process.exit(2);
}

const mac = crypto.createHash("sha256").update(appId + rawBody + timestamp + secret).digest("hex");
console.log("appId     :", appId);
console.log("timestamp :", timestamp);
console.log("MAC tính  :", mac);

if (sigHeader) {
  const received = sigHeader.replace(/^mac=/, "").trim();
  console.log("MAC nhận  :", received);
  const match = received.toLowerCase() === mac;
  console.log(match ? "✅ MATCH — secret + công thức đúng" : "❌ MISMATCH — sai secret hoặc sai công thức");
  process.exit(match ? 0 : 1);
}
