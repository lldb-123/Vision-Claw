import argparse
import json
import threading
from dataclasses import asdict
from .engine import SortEngine, load_config
from .client import ControllerClient
from .simulator import MockTransport, MockSTM32
from .vision import BasicDetector, DemoSource, ImageSource

def main():
    parser = argparse.ArgumentParser(description="智能分拣上位机")
    parser.add_argument("--headless", action="store_true", help="在命令行运行完整模拟流程")
    parser.add_argument("--drop-first-ack", action="store_true", help="模拟第一次 SORT 接收确认丢失")
    parser.add_argument("--image", help="分析图片，输出基础颜色与轮廓识别结果")
    args = parser.parse_args()
    config = load_config()
    detector = BasicDetector(config["vision"])
    if args.image:
        targets = detector.detect(ImageSource(args.image).read())
        print(json.dumps([asdict(target) for target in targets], ensure_ascii=False, indent=2))
    elif args.headless:
        device = MockSTM32(drop_first_ack=args.drop_first_ack)
        client = ControllerClient(MockTransport(device), config["serial"].copy())
        client.connect()
        engine = SortEngine(DemoSource(), detector, client, config,
                            emit=lambda event, value: print(value) if event == "state" else None)
        try:
            engine.run(threading.Event())
            print(json.dumps({"simulated": True, "completed": len(engine.records), "bins": engine.counts,
                              "physical_sort_calls": device.sort_executions}, ensure_ascii=False))
        finally:
            client.close()
    else:
        from .gui import launch
        launch()

if __name__ == "__main__":
    main()
