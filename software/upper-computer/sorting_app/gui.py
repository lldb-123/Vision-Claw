"""Tkinter 中文控制台。界面线程显示，工作线程负责设备与算法。"""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from .client import ControllerClient, TaskCancelled
from .engine import ROOT, load_config, SortEngine
from .simulator import MockTransport
from .transport import SerialTransport
from .vision import BasicDetector, DemoSource, ImageSource, CameraSource, CoordinateMapper, annotate

class App:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.worker = None
        self.closing = False
        self.source = self.client = self.engine = None
        self.detector = BasicDetector(self.config["vision"])
        self.raw = self.preview = None
        self.cal_points = None
        self.preview_geometry = None
        self.photos = []
        self.build()
        self.new_demo()
        self.root.after(40, self.poll)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        root = self.root
        root.title("智能分拣上位机 · 视觉与串口工作台")
        root.geometry(f"{min(1320, root.winfo_screenwidth()-80)}x{min(890, root.winfo_screenheight()-80)}")
        root.minsize(1050, 730)
        root.configure(bg="#EDF2F7")
        root.option_add("*Font", ("Microsoft YaHei UI", 10))
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#EDF2F7")
        style.configure("TLabel", background="#EDF2F7", foreground="#22384C")
        style.configure("TButton", padding=(12, 8), font=("Microsoft YaHei UI", 10))
        style.configure("Accent.TButton", background="#1464AB", foreground="white")
        style.map("Accent.TButton", background=[("active", "#0C4C89")])
        style.configure("Stop.TButton", foreground="#A33D20")
        style.configure("Treeview", rowheight=30, font=("Microsoft YaHei UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"), padding=7)

        top = ttk.Frame(root, padding=(24, 18, 24, 12))
        top.pack(fill="x")
        ttk.Label(top, text="智能分拣", font=("Microsoft YaHei UI", 23, "bold")).pack(side="left")
        ttk.Label(top, text="视觉与串口工作台", foreground="#657E92", padding=(18, 7)).pack(side="left")
        self.mode = tk.StringVar(value="模拟演示")
        ttk.Label(top, textvariable=self.mode, foreground="#1464AB", font=("Microsoft YaHei UI", 11, "bold")).pack(side="right")
        tools = ttk.Frame(root, padding=(24, 0, 24, 12))
        tools.pack(fill="x")
        self.idle_buttons = []
        for label, command in [("新建演示", self.new_demo), ("导入图片", self.open_image), ("相机拍照", self.open_camera), ("四点标定", self.begin_calibration)]:
            button = ttk.Button(tools, text=label, command=command)
            button.pack(side="left", padx=(0, 6))
            self.idle_buttons.append(button)
        self.port = tk.StringVar(value=self.config["serial"]["port"])
        ttk.Entry(tools, textvariable=self.port, width=10).pack(side="left", padx=(12, 6))
        for label, command in [("连接 STM32", self.connect_serial), ("回原点", self.home), ("查询状态", self.status)]:
            button = ttk.Button(tools, text=label, command=command)
            button.pack(side="left", padx=(0, 6))
            self.idle_buttons.append(button)

        content = ttk.Frame(root, padding=(24, 0, 24, 0))
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)
        left = ttk.Frame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        ttk.Label(left, text="托盘画面", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.canvas = tk.Canvas(left, bg="#E1E8EF", highlightthickness=0, height=380)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw_preview())
        self.canvas.bind("<Button-1>", self.calibration_click)
        self.picture_note = tk.StringVar(value="演示使用合成图形；真实物体需要补充形状和表面识别模型。")
        ttk.Label(left, textvariable=self.picture_note, foreground="#657E92", wraplength=650).pack(anchor="w", pady=(8, 5))

        right = ttk.Frame(content)
        right.grid(row=0, column=1, sticky="nsew")
        self.total = tk.StringVar(value="模拟入盒  0")
        ttk.Label(right, textvariable=self.total, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        self.state = tk.StringVar(value="准备就绪")
        ttk.Label(right, textvariable=self.state, wraplength=450, foreground="#1464AB").pack(anchor="w", pady=(6, 10))
        bins = ttk.Frame(right)
        bins.pack(fill="x")
        self.bin_labels = []
        for i in range(6):
            cell = tk.Label(bins, text=f"{i+1} 号盒\n0 件", bg="white", fg="#22384C", font=("Microsoft YaHei UI", 11), width=13, height=3)
            cell.grid(row=i//3, column=i%3, sticky="ew", padx=(0, 5), pady=(0, 5))
            bins.columnconfigure(i%3, weight=1)
            self.bin_labels.append(cell)
        recent = ttk.Frame(right)
        recent.pack(fill="x", pady=(8, 10))
        self.blank_photo = tk.PhotoImage(width=90, height=70)
        self.thumbnail = tk.Label(recent, image=self.blank_photo, bg="white", width=90, height=70)
        self.thumbnail.pack(side="left")
        self.last_label = tk.StringVar(value="等待第一件物体")
        ttk.Label(recent, textvariable=self.last_label, wraplength=270, padding=(12, 0)).pack(side="left")
        self.table = ttk.Treeview(right, columns=("id", "object", "box"), show="headings", height=5)
        for key, name, width in [("id", "序号", 50), ("object", "识别结果", 205), ("box", "盒号", 55)]:
            self.table.heading(key, text=name)
            self.table.column(key, width=width, anchor="w" if key == "object" else "center", stretch=key == "object")
        self.table.pack(fill="both", expand=True)
        actions = ttk.Frame(right, padding=(0, 12, 0, 0))
        actions.pack(fill="x")
        for text, one in [("自动运行", False), ("只处理一件", True)]:
            button = ttk.Button(actions, text=text, command=lambda single=one: self.run(single), style="Accent.TButton")
            button.pack(side="left", padx=(0, 7))
            self.idle_buttons.append(button)
        ttk.Button(actions, text="停止", command=self.stop, style="Stop.TButton").pack(side="right")

        log_area = ttk.Frame(root, padding=(24, 14, 24, 18))
        log_area.pack(fill="x")
        ttk.Label(log_area, text="通信与运行记录", foreground="#657E92").pack(anchor="w", pady=(0, 5))
        self.log = tk.Text(log_area, height=5, bg="#FFFFFF", fg="#40576A", relief="flat", padx=10, pady=8, font=("Consolas", 10), state="disabled")
        self.log.pack(fill="x")

    def publish(self, event, value):
        if event == "sorted":
            acknowledged = threading.Event()
            self.events.put((event, (value, acknowledged)))
            if not acknowledged.wait(2):
                raise RuntimeError("显示界面没有响应，已停止推进下一件")
        else:
            self.events.put((event, value))

    def trace(self, direction, frame):
        self.events.put(("log", f"{direction}  {frame}"))

    def start_worker(self, action):
        if self.worker and self.worker.is_alive():
            return
        self.cancel.clear()
        for button in self.idle_buttons:
            button.state(["disabled"])
        def work():
            try:
                action()
            except TaskCancelled as exc:
                self.publish("state", str(exc))
                self.publish("log", str(exc))
            except Exception as exc:
                self.publish("state", f"需要处理：{exc}")
                self.publish("log", f"ERROR  {type(exc).__name__}: {exc}")
            finally:
                self.events.put(("idle", None))
        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def replace_source(self, source):
        if self.source:
            self.source.close()
        self.source = source
        self.engine = SortEngine(source, self.detector, self.client, self.config, self.publish)

    def reset_view(self):
        self.table.delete(*self.table.get_children())
        self.total.set("模拟入盒  0" if self.source.is_demo else "已验证入盒  0")
        self.last_label.set("等待第一件物体")
        self.thumbnail.configure(image=self.blank_photo, width=90, height=70)
        for i, label in enumerate(self.bin_labels):
            label.configure(text=f"{i+1} 号盒\n0 件", bg="white")

    def new_demo(self):
        if self.client:
            self.client.close()
        self.client = ControllerClient(MockTransport(), self.config["serial"].copy(), self.trace)
        self.client.connect()
        self.replace_source(DemoSource())
        self.mode.set("模拟演示 · 合成图形")
        self.state.set("准备就绪，点击“自动运行”")
        self.reset_view()
        self.picture_note.set("12 个合成物体，按颜色与二维轮廓分入 6 个盒；模拟结果不代表实物识别准确率。")
        self.engine.snapshot()

    def open_image(self):
        path = filedialog.askopenfilename(title="选择托盘照片", filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")])
        if not path:
            return
        def action():
            source = ImageSource(path)
            self.replace_source(source)
            self.publish("mode", "图片分析")
            self.publish("reset", None)
            self.engine.snapshot()
            self.publish("state", "已完成基础颜色与轮廓分析")
            self.publish("note", "图片分析仅输出可见颜色和二维轮廓，表面信息默认为未知。")
        self.start_worker(action)

    def open_camera(self):
        def action():
            if not isinstance(self.source, CameraSource):
                source = CameraSource(**self.config["camera"])
                self.replace_source(source)
                self.publish("reset", None)
            self.publish("mode", "相机拍摄")
            self.engine.snapshot()
            self.publish("state", "相机图像已更新")
            self.publish("note", "相机每次拍照更新画面；正式分拣需完成标定并接入经过实物验证的识别器。")
        self.start_worker(action)

    def connect_serial(self):
        port = self.port.get().strip()
        def action():
            transport = SerialTransport(port, self.config["serial"]["baudrate"])
            client = ControllerClient(transport, self.config["serial"].copy(), self.trace)
            try:
                result = client.connect()
            except Exception:
                transport.close()
                raise
            if self.client:
                self.client.close()
            self.client = client
            self.engine.client = client
            self.publish("mode", "真实串口已连接")
            self.publish("state", f"已连接 {port}，启动标识 {result.args[1]}")
        self.start_worker(action)

    def home(self):
        def action():
            self.publish("state", "正在回原点")
            self.client.execute("HOME", cancel=self.cancel)
            self.publish("state", "回原点完成")
        self.start_worker(action)

    def status(self):
        def action():
            result = self.client.status()
            self.publish("state", f"设备 {result.args[0]}，任务 {result.args[1]}，已回零 {result.args[2]}")
        self.start_worker(action)

    def run(self, one):
        # 演示坐标只能连接模拟设备，避免将合成目标发送给真实电机。
        if self.source.is_demo and not isinstance(self.client.transport, MockTransport):
            self.state.set("当前是合成画面，请先切换到相机，或点击“新建演示”")
            return
        if not self.source.is_demo and isinstance(self.client.transport, MockTransport):
            self.state.set("真实图像需要连接 STM32；模拟流程请点击“新建演示”")
            return
        self.start_worker(lambda: self.engine.run(self.cancel, one=one))

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.cancel.set()
            self.state.set("正在请求停止")
        elif self.client:
            self.start_worker(lambda: (self.client.stop(), self.publish("state", "停止指令已确认")))

    def begin_calibration(self):
        if self.raw is None or self.source.is_demo:
            self.state.set("请先导入真实托盘照片或拍摄相机画面")
            return
        self.cal_points = []
        self.state.set("依次点击托盘：左上、右上、右下、左下；尺寸取自配置文件")
        self.draw_preview()

    def calibration_click(self, event):
        if self.cal_points is None or self.preview_geometry is None:
            return
        scale, ox, oy, w, h = self.preview_geometry
        if not (ox <= event.x < ox+w and oy <= event.y < oy+h):
            return
        self.cal_points.append(((event.x-ox)/scale, (event.y-oy)/scale))
        self.draw_preview()
        if len(self.cal_points) == 4:
            try:
                width = self.config["calibration"]["width_mm"]
                height = self.config["calibration"]["height_mm"]
                mapper = CoordinateMapper(self.cal_points, [[0, height], [width, height], [width, 0], [0, 0]])
                mapper.save(ROOT / "configs/calibration.json", (self.raw.shape[1], self.raw.shape[0]))
                self.state.set(f"已保存平面标定：{width:g} × {height:g} mm；请用实测点复核")
            except Exception as exc:
                self.state.set(f"标定失败：{exc}")
            self.cal_points = None

    def draw_preview(self):
        if self.preview is None:
            return
        cw, ch = max(self.canvas.winfo_width(), 100), max(self.canvas.winfo_height(), 100)
        ih, iw = self.preview.shape[:2]
        scale = min(cw/iw, ch/ih)
        w, h = max(1, round(iw*scale)), max(1, round(ih*scale))
        frame = cv2.resize(self.preview, (w, h))
        self.preview_photo = tk.PhotoImage(data=cv2.imencode(".png", frame)[1].tobytes())
        ox, oy = (cw-w)/2, (ch-h)/2
        self.canvas.delete("all")
        self.canvas.create_image(ox, oy, anchor="nw", image=self.preview_photo)
        self.preview_geometry = (scale, ox, oy, w, h)
        for i, point in enumerate(self.cal_points or []):
            x, y = point[0]*scale+ox, point[1]*scale+oy
            self.canvas.create_oval(x-6, y-6, x+6, y+6, fill="#E77825", outline="white", width=2)
            self.canvas.create_text(x+15, y-12, text=str(i+1), fill="#B4440C", font=("Arial", 14, "bold"))

    def poll(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "frame":
                    self.raw, self.preview = value["raw"], value["image"]
                    self.draw_preview()
                elif event in ("state", "mode", "note"):
                    {"state": self.state, "mode": self.mode, "note": self.picture_note}[event].set(value)
                elif event == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", value + "\n")
                    if int(self.log.index("end-1c").split(".")[0]) > 180:
                        self.log.delete("1.0", "60.0")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif event == "reset":
                    self.reset_view()
                elif event == "sorted":
                    data, acknowledged = value
                    try:
                        record = data["record"]
                        self.total.set(f"{'模拟入盒' if record['simulated'] else '已验证入盒'}  {record['index']}")
                        self.table.insert("", "end", values=(record["index"], record["label"], record["box"]))
                        self.table.yview_moveto(1)
                        self.last_label.set(f"{record['label']}\n存入 {record['box']} 号盒   累计 {record['index']} 件")
                        for i, count in enumerate(data["counts"]):
                            self.bin_labels[i].configure(text=f"{i+1} 号盒\n{count} 件", bg="#DAEAF7" if count else "white")
                        thumb = cv2.resize(data["thumbnail"], (80, 70))
                        self.thumb_photo = tk.PhotoImage(data=cv2.imencode(".png", thumb)[1].tobytes())
                        self.thumbnail.configure(image=self.thumb_photo, width=90, height=70)
                        self.root.update_idletasks()
                    finally:
                        acknowledged.set()
                elif event == "idle":
                    for button in self.idle_buttons:
                        button.state(["!disabled"])
                    if self.closing:
                        self.finish_close()
                        return
        except queue.Empty:
            pass
        self.root.after(40, self.poll)

    def close(self):
        if self.worker and self.worker.is_alive():
            self.closing = True
            self.cancel.set()
            self.state.set("正在停止任务并关闭")
        else:
            self.finish_close()

    def finish_close(self):
        if self.source:
            self.source.close()
        if self.client:
            self.client.close()
        self.root.destroy()

def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()
