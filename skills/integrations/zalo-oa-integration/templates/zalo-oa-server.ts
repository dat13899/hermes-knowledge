/**
 * Zalo OA Bot — Express server template hoàn chỉnh.
 * Copy vào project + thêm .env (xem SKILL.md bảng credentials).
 *
 * Tính năng: webhook nhận tin + verify signature (luôn 200) + AI reply + auto-refresh token + log file + trang log public.
 */
import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import crypto from "node:crypto";
import fs from "node:fs";

dotenv.config();

// ===== Config =====
const PORT = Number(process.env.PORT || 4810);
const ZALO_APP_ID = process.env.ZALO_APP_ID || "";
const ZALO_OA_SECRET_KEY = process.env.ZALO_OA_SECRET_KEY || ""; // oa.zalo.me → Công cụ lập trình
const ZALO_ACCESS_TOKEN = process.env.ZALO_ACCESS_TOKEN || "";
const ZALO_REFRESH_TOKEN = process.env.ZALO_REFRESH_TOKEN || "";
const AI_URL = process.env.OMNIROUTE_URL || "http://localhost:20128/v1";
const AI_MODEL = process.env.AI_MODEL || "cmd/deepseek/deepseek-v4-flash";

// ===== Log file (background stdout bị buffer — phải ghi file) =====
const LOG_FILE = "C:/Users/datel/zalo-oa-bot/webhook.log";
function log(msg: string) {
  const normalized = msg.replace(/^\[([a-zA-Z]+)\]\s*/, (_m: string, t: string) => `[${t.toUpperCase()}] `);
  const line = `[${new Date().toISOString()}] ${normalized}\n`;
  try { fs.appendFileSync(LOG_FILE, line); } catch {}
  console.log(msg);
}

// ===== Verify signature =====
// Header: X-ZEvent-Signature: mac=<hex>
// mac = hmac_sha256(OAsecretKey, appId + rawBody + timestamp)
// timestamp nằm TRONG BODY (payload.timestamp, ms) — không phải header!
function verifyZaloSignature(rawBody: string, appId: string, timestamp: string, signature: string): boolean {
  if (!rawBody || !appId || !timestamp || !signature) return false;
  const cleanSig = signature.startsWith("mac=") ? signature.slice(4) : signature;
  const mac = crypto.createHmac("sha256", ZALO_OA_SECRET_KEY).update(appId + rawBody + timestamp).digest("hex");
  const received = Buffer.from(cleanSig, "hex");
  const expected = Buffer.from(mac, "hex");
  if (received.length !== expected.length) return false;
  return crypto.timingSafeEqual(received, expected);
}

// ===== Refresh token (access token chỉ sống 25h) =====
async function refreshZaloToken(): Promise<boolean> {
  try {
    const body = new URLSearchParams({
      app_id: ZALO_APP_ID,
      grant_type: "refresh_token",
      refresh_token: ZALO_REFRESH_TOKEN,
    });
    const res = await fetch("https://oauth.zaloapp.com/v4/oa/refresh_token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    const data = (await res.json()) as any;
    if (!data.access_token) { log(`[TOKEN] refresh failed: ${data.error} ${data.message}`); return false; }
    // Refresh token dùng 1 lần — persist ngay
    const env = fs.readFileSync("C:/Users/datel/zalo-oa-bot/.env", "utf8");
    const set = (k: string, v: string) => {
      const re = new RegExp(`^${k}=.*$`, "m");
      return re.test(env) ? env.replace(re, `${k}=${v}`) : env + `\n${k}=${v}`;
    };
    let next = set("ZALO_ACCESS_TOKEN", data.access_token);
    if (data.refresh_token) next = set("ZALO_REFRESH_TOKEN", data.refresh_token);
    fs.writeFileSync("C:/Users/datel/zalo-oa-bot/.env", next, "utf8");
    process.env.ZALO_ACCESS_TOKEN = data.access_token;
    if (data.refresh_token) process.env.ZALO_REFRESH_TOKEN = data.refresh_token;
    log("[TOKEN] refreshed OK");
    return true;
  } catch (e: any) { log(`[TOKEN] refresh error: ${e.message}`); return false; }
}

// ===== Gửi tin =====
async function sendText(userId: string, text: string): Promise<void> {
  try {
    let res = await fetch("https://openapi.zalo.me/v3.0/oa/message/cs", {
      method: "POST",
      headers: { "Content-Type": "application/json", access_token: process.env.ZALO_ACCESS_TOKEN || "" },
      body: JSON.stringify({ recipient: { user_id: userId }, message: { text: text.slice(0, 2000) } }),
    });
    let data = (await res.json()) as any;
    // Token hết hạn → refresh + gửi lại 1 lần
    if (data.error && [-216, -124, -221, -222].includes(data.error)) {
      log(`[SEND] token error ${data.error}, refreshing...`);
      if (await refreshZaloToken()) {
        res = await fetch("https://openapi.zalo.me/v3.0/oa/message/cs", {
          method: "POST",
          headers: { "Content-Type": "application/json", access_token: process.env.ZALO_ACCESS_TOKEN || "" },
          body: JSON.stringify({ recipient: { user_id: userId }, message: { text: text.slice(0, 2000) } }),
        });
        data = await res.json();
      }
    }
    if (data.error) { log(`[SEND] failed: ${data.error} ${data.message}`); return; }
    log(`[SEND] ok msg_id=${data.data?.message_id} quota=${data.data?.quota?.remain}`);
  } catch (e: any) { log(`[SEND] error: ${e.message}`); }
}

// ===== AI reply =====
async function askAi(userText: string): Promise<string> {
  try {
    const res = await fetch(`${AI_URL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: AI_MODEL, messages: [{ role: "system", content: "Bạn là trợ lý ảo Zalo OA. Trả lời ngắn gọn tiếng Việt." }, { role: "user", content: userText }], max_tokens: 500 }),
    });
    const raw = await res.text();
    // OmniRoute trả SSE dù stream:false — ghép delta content
    let content = "";
    if (raw.trim().startsWith("{")) {
      content = JSON.parse(raw).choices?.[0]?.message?.content || "";
    } else {
      for (const line of raw.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        const p = line.slice(6).trim();
        if (p === "[DONE]") continue;
        try { content += JSON.parse(p).choices?.[0]?.delta?.content || ""; } catch {}
      }
    }
    return content.trim() || "Xin lỗi, tôi đang gặp sự cố. Bạn thử lại nhé!";
  } catch (e: any) { log(`[AI] error: ${e.message}`); return "Xin lỗi, tôi đang gặp sự cố."; }
}

// ===== Server =====
const app = express();
app.use(cors());
// Bắt rawBody qua verify callback — KHÔNG dùng req.on('data') (express consume trước → treo)
app.use(express.json({ verify: (req: any, _res: any, buf: Buffer) => { req.rawBody = buf.toString("utf8"); } }));

// Trang chủ: HTML có meta verification Zalo (bắt buộc để xác minh website)
app.get("/", (_req, res) => {
  res.type("html").send(`<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"/>
  <meta name="zalo-platform-site-verification" content="REPLACE_WITH_YOUR_META"/>
  <title>Zalo OA Bot</title></head><body><h1>Zalo OA Bot OK</h1></body></html>`);
});

// Webhook chính — LUÔN trả 200, ≤2s, xử lý async
app.post("/zalo/webhook", (req, res) => {
  const rawBody = (req as any).rawBody as string;
  const signature = (req.headers["x-zevent-signature"] as string) || "";

  let payload: any = null;
  try { payload = JSON.parse(rawBody); } catch { return res.status(200).json({ ok: true }); }

  const timestamp = payload.timestamp || "";
  log(`[WEBHOOK] received event=${payload.event_name} from=${payload.sender?.id} text=${payload.message?.text?.slice(0, 50)}`);
  log(`[WEBHOOK] FULL_BODY=${rawBody}`);

  // Sai signature → log + bỏ qua, VẪN 200
  if (!verifyZaloSignature(rawBody, ZALO_APP_ID, timestamp, signature)) {
    log("[WEBHOOK] signature invalid — ignored (still 200)");
    return res.status(200).json({ ok: true });
  }

  res.status(200).json({ ok: true }); // respond ngay

  // Xử lý bất đồng bộ
  if (payload.event_name === "user_send_text" && payload.sender?.id) {
    const userId = payload.sender.id;
    const text = payload.message?.text?.trim() || "";
    log(`[EVENT] user=${userId} text=${text.slice(0, 60)}`);
    askAi(text).then((reply) => {
      log(`[AI] reply=${reply.slice(0, 60)}`);
      return sendText(userId, reply);
    });
  }
});

app.listen(PORT, () => log(`Zalo OA Bot listening on :${PORT}`));
