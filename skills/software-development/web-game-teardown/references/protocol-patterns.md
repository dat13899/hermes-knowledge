# Protocol Patterns Found in HTML5 Games

Common networking patterns discovered during teardowns. Use as a reference to quickly identify what you're looking at.

## XOR + Snappy (Frost Kingdom / Chinese SLG standard)

**Obfuscation, NOT encryption.** Found in ByteArrayMsg module.

```
Send path:
  JSON.stringify(msg) → SnappyJS.compress → XOR each byte with (length - position) → WebSocket.send

Receive path:
  WebSocket.onmessage → XOR each byte with (length - position) → SnappyJS.uncompress → JSON.parse → { "S2C_Name": {...} }
```

Key code (deobfuscated):
```js
// Decode: XOR + Snappy
for (rByte.position = 0; rByte.position < t; ) {
    let byte = rByte.readByte();
    rByte.position -= 1;
    byte ^= t - rByte.position;   // key = message length
    rByte.writeByte(byte);
}
let decompressed = SnappyJS.uncompress(rByte.bytes);
let json = JSON.parse(decompressed);
let msgName = Object.keys(json)[0];  // e.g. "S2C_Login"
MessageCenter.dispatch(msgName, json[msgName]);

// Encode: Snappy + XOR
sByte.writeUTFBytes(jsonString);
let compressed = SnappyJS.compress(sByte.bytes);
// then XOR same way, write back, websocket.send
```

**Implications:**
- Trivially reversible (Snappy is a public algorithm, XOR key is derived from length)
- No MITM protection — any proxy can read/write messages
- But this only reveals traffic content; it doesn't help cheat if server is authoritative
- Often paired with `ws://` (no TLS), meaning traffic is completely exposed

## WebSocket wrapper (egret-style)
- `EWebSocket` extends `cc.EventTarget` — event-driven (`CONNECT`, `CLOSE`, `SOCKET_DATA`, `IO_ERROR`)
- `HTML5Websocket` — thin wrapper around native `WebSocket`
- `Connection` — manages connect/reconnect, wraps `EWebSocket` + `ByteArrayMsg`
- `MessageCenter` — event bus dispatching `S2C_*` messages to registered handlers

## Message naming convention
- `C2S_*` — client-to-server requests
- `S2C_*` — server-to-client responses/notifications  
- `ns.msg.*` — generated classes (typically empty, just ClassName strings)
- `ns.loginmsg.*` — login-specific message namespace
- `ns.e.*` — client-side event constants (non-network)

## Ping mechanism
- `C2S_WG` + `S2C_WG` — heartbeat with round-trip timing
- `_wgTime` accumulator: send WG every ~1900ms (on MainControl.update tick)
- Ping data used for latency display; excluded from debug logging
