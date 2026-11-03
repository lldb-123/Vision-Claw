import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from sorting_app.protocol import Packet, FrameDecoder, crc16
from sorting_app.client import ControllerClient, DeviceError, TaskCancelled
from sorting_app.simulator import MockSTM32, MockTransport
from sorting_app.vision import BasicDetector, DemoSource, CoordinateMapper
from sorting_app.engine import SortEngine, load_config

class ProtocolTests(unittest.TestCase):
    def test_known_crc_and_example(self):
        self.assertEqual(crc16(b"123456789"), 0x29B1)
        packet = Packet("7A1C9E20", 12, "SORT", ("12500", "8000", "2"))
        self.assertEqual(packet.encode(), b"@1,7A1C9E20,12,SORT,12500,8000,2*49A9\r\n")

    def test_fragmented_corrupt_and_concatenated_frames(self):
        packet = Packet("7A1C9E20", 12, "SORT", ("12500", "8000", "2"))
        good = packet.encode()
        bad = good.replace(b"12500", b"12501")
        stream = b"noise" + b"@" + b"x" * 300 + bad + good + good
        decoder = FrameDecoder()
        result = []
        for offset in range(0, len(stream), 7):
            result.extend(decoder.feed(stream[offset:offset+7]))
        self.assertEqual(result, [packet, packet])
        self.assertEqual(decoder.errors, 2)

class IntegrationTests(unittest.TestCase):
    def make_client(self, **kwargs):
        device = MockSTM32(duration=0.04, **kwargs)
        client = ControllerClient(MockTransport(device), {"ack_timeout": 0.03, "retries": 2, "motion_timeout": 2})
        client.connect()
        client.execute("HOME")
        return device, client

    def test_retransmission_executes_only_once(self):
        device, client = self.make_client(drop_first_ack=True)
        device.duration = 0.1
        reply = client.execute("SORT", 10000, 10000, 1)
        self.assertEqual(reply.args, ("SORT", "ENTRY_VERIFIED"))
        self.assertEqual(device.sort_executions, 1)
        request, _ = device.records[reply.seq]
        device.handle(request)
        self.assertEqual(device.sort_executions, 1)
        conflict = Packet(client.session, request.seq, "SORT", ("0", "0", "2"))
        device.handle(conflict)
        self.assertEqual(Packet.decode(device.outbox[-1]).args[-1], "ID_CONFLICT")

    def test_lost_terminal_reply_recovered_without_reexecuting(self):
        device, client = self.make_client(drop_first_done=True)
        reply = client.execute("SORT", 10000, 10000, 1)
        self.assertEqual(reply.args[-1], "ENTRY_VERIFIED")
        self.assertEqual(device.sort_executions, 1)

    def test_stop_interrupts_motion(self):
        device, client = self.make_client()
        device.duration = 2
        cancel = threading.Event()
        timer = threading.Timer(0.06, cancel.set)
        timer.start()
        with self.assertRaises(TaskCancelled):
            client.execute("SORT", 10000, 10000, 1, cancel=cancel)
        timer.join()
        self.assertIsNone(device.active)
        self.assertFalse(client.homed)

    def test_full_demo_12_items_six_boxes(self):
        device, client = self.make_client()
        config = load_config()
        source = DemoSource()
        with tempfile.TemporaryDirectory() as directory, patch("sorting_app.engine.ROOT", Path(directory)):
            engine = SortEngine(source, BasicDetector(), client, config)
            engine.run(threading.Event())
            self.assertEqual(engine.counts, [2] * 6)
            self.assertEqual(len(engine.records), 12)
            self.assertEqual(device.sort_executions, 12)
            self.assertEqual(len(source.objects), 0)

    def test_failed_drop_does_not_count_or_remove_object(self):
        _, client = self.make_client(fail_sort=True)
        source = DemoSource()
        engine = SortEngine(source, BasicDetector(), client)
        with self.assertRaises(DeviceError):
            engine.run(threading.Event())
        self.assertEqual(engine.counts, [0] * 6)
        self.assertEqual(len(source.objects), 12)

    def test_boot_change_is_detected(self):
        device, client = self.make_client()
        device.boot_id = "00000000"
        with self.assertRaisesRegex(DeviceError, "重启"):
            client.status()

    def test_calibration_and_unknown_surface(self):
        source = DemoSource()
        x, y = source.mapper.convert((380, 300))
        self.assertAlmostEqual(x, 130, places=3)
        self.assertAlmostEqual(y, 130, places=3)
        target = BasicDetector().detect(source.read())[0]
        with self.assertRaisesRegex(ValueError, "识别器"):
            target.category(demo=False)

if __name__ == "__main__":
    unittest.main()
