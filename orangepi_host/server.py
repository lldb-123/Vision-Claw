#!/usr/bin/env python3
import argparse, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from controller import Controller

HTML = r'''<!doctype html><html lang="zh-CN"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VisionClaw 上位控制</title><style>
:root{font-family:Arial,sans-serif;color:#e8eef7;background:#101722}body{margin:0;padding:16px;max-width:1100px;margin:auto}h1{font-size:24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}.card{background:#1b2635;border:1px solid #304157;border-radius:12px;padding:14px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}button,input{font-size:18px;padding:10px;border-radius:8px;border:1px solid #50637b;background:#243449;color:#fff}button{cursor:pointer}button.danger{background:#a52b2b}.value{font-family:monospace;color:#a9e6bd}.muted{color:#9cadc2;font-size:13px}#log{white-space:pre-wrap;max-height:140px;overflow:auto;font-family:monospace;font-size:12px}</style>
<body><h1>VisionClaw 上位控制</h1><div class="card"><div id="conn">连接中</div><div class="muted">Z 轴为无位置反馈，托盘为开环控制</div></div><div class="grid"><div class="card"><h2>X 轴</h2><div id="x"></div><div class="row"><button onclick="cmd('ENABLE X')">使能</button><button onclick="cmd('HOME X')">回零</button><button onclick="move('X',-10)">← 10mm</button><button onclick="move('X',10)">10mm →</button></div></div><div class="card"><h2>Y 轴</h2><div id="y"></div><div class="row"><button onclick="cmd('ENABLE Y')">使能</button><button onclick="cmd('HOME Y')">回零</button><button onclick="move('Y',-10)">← 10mm</button><button onclick="move('Y',10)">10mm →</button></div></div><div class="card"><h2>Z 舵机</h2><div id="z"></div><div class="row"><button onclick="cmd('Z UP')">上升</button><button onclick="cmd('Z DOWN')">下降</button><button onclick="cmd('STOP Z')">停止</button><input id="pulse" type="number" value="1500" min="500" max="2500"><button onclick="cmd('SERVO Z '+document.querySelector('#pulse').value+' 700')">设置脉宽</button></div></div><div class="card"><h2>底部托盘</h2><div id="tray"></div><div class="row"><button onclick="cmd('TRAY CCW 20 1000')">逆时针</button><button onclick="cmd('TRAY CW 20 1000')">顺时针</button><button onclick="cmd('TRAY STOP')">停止</button></div></div></div><div class="card"><div class="row"><button class="danger" onclick="cmd('ESTOP')">急停</button><button onclick="cmd('CLEAR')">清除急停</button><button onclick="cmd('STATUS')">刷新状态</button></div><div id="log"></div></div><script>
async function api(path,body){let r=await fetch(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body||{})});let j=await r.json();log(j);return j}function cmd(command){return api('/api/command',{command})}function move(a,v){return cmd('MOVE_MM '+a+' '+v+' 5')}function log(v){let e=document.querySelector('#log');e.textContent=(new Date().toLocaleTimeString())+' '+JSON.stringify(v)+'\n'+e.textContent}function render(s){document.querySelector('#conn').textContent=(s.connected?'已连接':'未连接')+(s.simulation?' · 模拟模式':''); for(let a of ['x','y']){let d=s.axes[a.toUpperCase()];document.querySelector('#'+a).innerHTML=`位置 <b class=value>${d.pos_mm} mm</b> · 目标 ${d.target} · 状态 ${d.state}<br>使能 ${d.enabled?'是':'否'} · 已回零 ${d.homed?'是':'否'}`}document.querySelector('#z').innerHTML=`当前 ${s.z.pulse_us} μs · 目标 ${s.z.target_us} μs · 忙 ${s.z.busy?'是':'否'}`;document.querySelector('#tray').innerHTML=`状态 ${s.tray.state} · 速度 ${s.tray.speed} · 剩余 ${s.tray.remaining_ms} ms`}async function poll(){try{let s=await (await fetch('/api/state')).json();render(s)}catch(e){}}setInterval(poll,1000);poll();
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    controller = None
    def _json(self, data, status=200):
        raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if urlparse(self.path).path == '/':
            raw=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        elif self.path == '/api/state': self._json(self.controller.snapshot())
        else: self._json({'error':'not found'},404)
    def do_POST(self):
        if self.path != '/api/command': self._json({'error':'not found'},404); return
        try: n=int(self.headers.get('Content-Length','0')); body=json.loads(self.rfile.read(n)); result=self.controller.send(body['command']); self._json({'result':result,'command':body['command']})
        except Exception as exc: self._json({'error':str(exc)},400)
    def log_message(self, *_): pass

def main():
    p=argparse.ArgumentParser(); p.add_argument('--device',default=os.getenv('VISIONCLAW_SERIAL','/dev/ttyS3')); p.add_argument('--port',type=int,default=int(os.getenv('VISIONCLAW_PORT','8080'))); p.add_argument('--simulation',action='store_true'); a=p.parse_args()
    Handler.controller=Controller(a.device,simulation=a.simulation); server=ThreadingHTTPServer(('0.0.0.0',a.port),Handler)
    try: print(f'VisionClaw host listening on :{a.port}'); server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close(); Handler.controller.close()
if __name__=='__main__': main()
