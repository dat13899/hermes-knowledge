#!/usr/bin/env node
/**
 * Tính X-ZEvent-Signature theo công thức Zalo để test webhook cục bộ.
 * mac = HMAC-SHA256(OAsecretKey, appId + body + timestamp)
 *
 * Usage:
 *   node scripts/zalo-signature-test.js <oaSecretKey> <appId> <timestamp> <bodyFile>
 *   (bodyFile chứa JSON body — dùng file để tránh lệch encoding tiếng Việt qua shell)
 *
 * Không có args → dùng payload mẫu từ docs.
 */
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

let appId, oaSecret, ts, body;
if (process.argv.length >= 6) {
  oaSecret = process.argv[2];
  appId = process.argv[3];
  ts = process.argv[4];
  body = fs.readFileSync(path.resolve(process.argv[5]), "utf8").trim();
} else {
  // Payload mẫu từ docs (ASCII để tránh encoding issue trên Windows bash)
  appId = "360846524940903967";
  oaSecret = "mysecretkey";
  ts = "154390853474";
  body = JSON.stringify({
    app_id: appId,
    sender: { id: "246845883529197922" },
    recipient: { id: "388613280878808645" },
    event_name: "user_send_text",
    message: { text: "hello", msg_id: "96d3cdf3af150460909" },
    timestamp: ts,
  });
}

const mac = crypto.createHmac("sha256", oaSecret).update(appId + body + ts).digest("hex");
console.log("APP_ID:", appId);
console.log("BODY:", body);
console.log("MAC:", mac);
console.log("\nTest:");
console.log(`  curl -X POST http://localhost:4810/zalo/webhook \\`);
console.log(`    -H "Content-Type: application/json" \\`);
console.log(`    -H "X-ZEvent-Signature: ${mac}" \\`);
console.log(`    -H "X-ZEvent-Timestamp: ${ts}" \\`);
console.log(`    -d '${body}'`);
