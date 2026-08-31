// verify-webgl-module.cjs — chạy inline ES module (scrollytelling HTML) với Three.js
// thật + WebGL mock, bắt runtime error KHÔNG cần GPU. Đã bắt được hoisting bug
// (`animate3D is not defined` — function trong block if không được hoisted).
//
// Usage:
//   node scripts/verify-webgl-module.cjs <page.html> <three.module.js path>
//   (three lấy từ `npm install --no-save three@0.160.0`; xong có thể uninstall,
//   trang thật dùng CDN)
//
// Nếu module chạy sạch: "✅ 3D MODULE EXECUTED WITHOUT ERROR" + số RAF frames.
const fs = require('fs');
const path = require('path');

const [htmlPath, threePath] = process.argv.slice(2);
if (!htmlPath || !threePath) {
  console.error('Usage: node verify-webgl-module.cjs <page.html> <three.module.js>');
  process.exit(1);
}

// ── minimal DOM mock ──
class MockEl {
  constructor(tag) {
    this.tagName = (tag || 'div').toUpperCase();
    this.children = [];
    this.style = {};
    this.classList = { add(){}, remove(){}, toggle(){} };
    this.attributes = {};
    this.listeners = {};
    this.textContent = '';
    this.dataset = {};
    this.userData = {};
    this.isPoints = false; this.isMesh = false; this.isSprite = false; this.isLineSegments = false; this.isLine = false; this.isGroup = true;
    this.material = { opacity: 1, needsUpdate: false };
    this.geometry = { attributes: {} };
    this.visible = true;
    this.position = { set(){}, x:0, y:0, z:0 };
    this.rotation = { set(){}, x:0, y:0, z:0 };
    this.scale = { setScalar(){} };
    this.offsetTop = 0;
    this.querySelector = () => ({ style: {}, textContent: '' });
    this.querySelectorAll = () => [];
    this.addEventListener = () => {};
    this.scrollIntoView = () => {};
    this.append = (...c) => { this.children.push(...c); };
    this.appendChild = (c) => { this.children.push(c); return c; };
    this.remove = () => {};
    this.clear = () => {};
    this.getContext = () => mockGL;
    this.setAttribute = (k, v) => { this.attributes[k] = v; };
    this.getAttribute = () => null;
    this.width = 300; this.height = 150;
  }
}

// mock WebGL context (đủ cho three WebGLRenderer chạy được render loop)
const mockGL = {
  getParameter: () => 'WebGL 1.0 (mock)',
  VERSION: 'WebGL 1.0',
  ACTIVE_UNIFORMS: 0x8B86, ACTIVE_ATTRIBS: 0x8B89, LINK_STATUS: 0x8B82, COMPILE_STATUS: 0x8B81,
  getExtension: () => null,
  createBuffer: () => ({}), bindBuffer(){}, bufferData(){}, bufferSubData(){},
  createTexture: () => ({}), bindTexture(){}, texImage2D(){}, texParameteri(){}, generateMipmap(){},
  createProgram: () => ({}), createShader: () => ({}), shaderSource(){}, compileShader(){},
  attachShader(){}, linkProgram(){}, useProgram(){}, getProgramParameter: (pname) => pname === 0x8B86 ? 1 : (pname === 0x8B89 ? 0 : true),
  getShaderParameter: () => true, getUniformLocation: () => ({}), getAttribLocation: () => 0,
  uniform1f(){}, uniform2f(){}, uniform3f(){}, uniform4f(){}, uniform1i(){}, uniformMatrix4fv(){},
  enableVertexAttribArray(){}, vertexAttribPointer(){}, drawArrays(){}, drawElements(){},
  viewport(){}, clearColor(){}, clear(){}, enable(){}, disable(){}, blendFunc(){},
  depthFunc(){}, activeTexture(){}, uniformMatrix3fv(){}, pixelStorei(){},
  clearDepth(){}, depthMask(){}, colorMask(){}, clearStencil(){}, stencilFunc(){},
  stencilMask(){}, stencilOp(){}, cullFace(){}, frontFace(){}, blendEquation(){},
  blendEquationSeparate(){}, blendFuncSeparate(){}, sampleCoverage(){}, lineWidth(){},
  getShaderInfoLog: () => '', getProgramInfoLog: () => '',
  deleteShader(){}, deleteProgram(){}, deleteBuffer(){}, deleteTexture(){},
  deleteFramebuffer(){}, deleteRenderbuffer(){}, deleteVertexArray(){},
  isShader: () => true, isProgram: () => true,
  createFramebuffer: () => ({}), createRenderbuffer: () => ({}),
  framebufferTexture2D(){}, renderbufferStorage(){}, framebufferRenderbuffer(){},
  bindFramebuffer(){}, bindRenderbuffer(){}, checkFramebufferStatus: () => 0x8CD5,
  getUniform: () => null,
  getActiveUniform: () => ({name: 'mockUniform', size: 1, type: 5126}),
  getActiveAttrib: () => ({name: 'mockAttrib', size: 1, type: 5126}),
  canvas: { width: 300, height: 150 },
  getContextAttributes: () => ({}),
  isContextLost: () => false,
};

// mock 2D context (cho glowTexture canvas)
const mock2D = {
  createRadialGradient: () => ({ addColorStop(){} }),
  fillRect(){},
  set fillStyle(v){}, get fillStyle(){ return ''; },
  measureText: () => ({ width: 10 }),
};

const el = (tag) => new MockEl(tag);
const canvasEl = new MockEl('canvas');
canvasEl.getContext = (type) => type === '2d' ? mock2D : mockGL;

// global mocks — ĐIỀU CHỈNH theo id/class của trang của bạn:
global.document = {
  querySelector: (sel) => {
    if (sel === '#c' || sel === 'canvas') return canvasEl;
    if (sel === '#cur' || sel === '#rail' || sel === '#hint' || sel === '#progress') return new MockEl('div');
    return new MockEl('div');
  },
  querySelectorAll: (sel) => {
    if (sel === '.chapter') return Array.from({length: 6}, () => new MockEl('section'));
    return [];
  },
  createElement: (tag) => tag === 'canvas' ? canvasEl : el(tag),
  body: new MockEl('body'),
  documentElement: { scrollHeight: 4000, clientHeight: 800 },
  addEventListener: () => {},
  getElementById: () => new MockEl('div'),
};
global.window = {
  innerWidth: 1280, innerHeight: 800, devicePixelRatio: 1, scrollY: 0,
  addEventListener: () => {},
  requestAnimationFrame: (cb) => { global.__rafCount = (global.__rafCount||0)+1; if (global.__rafCount < 3) cb(); },
};
global.addEventListener = () => {};
global.requestAnimationFrame = global.window.requestAnimationFrame;
global.HTMLCanvasElement = function(){};
global.HTMLButtonElement = function(){};
global.navigator = { userAgent: 'node-test' };

// extract inline module script (bỏ qua script có src)
const html = fs.readFileSync(htmlPath, 'utf8');
const m = html.match(/<script type="module">([\s\S]*?)<\/script>/);
if (!m) { console.error('❌ NO INLINE MODULE FOUND in', htmlPath); process.exit(1); }

// replace bare 'three' import với file:// URL
const threeURL = 'file:///' + path.resolve(threePath).replace(/\\/g, '/');
const code = m[1].replace(/from 'three'/, `from '${threeURL}'`);

(async () => {
  try {
    await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));
    await new Promise(r => setTimeout(r, 100));
    console.log('✅ 3D MODULE EXECUTED WITHOUT ERROR');
    console.log('✅ RAF FRAMES:', global.__rafCount || 0);
  } catch (e) {
    console.error('❌ 3D MODULE ERROR:', e.message);
    console.error(e.stack.split('\n').slice(0, 6).join('\n'));
    process.exit(1);
  }
})();
