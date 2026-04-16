import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from disk_scheduler import DiskScheduler, SimulationRequest, load_request, main


class DiskSchedulerTestCase(unittest.TestCase):
    def test_fcfs_and_sstf_orders_are_deterministic(self) -> None:
        request = SimulationRequest(start=50, requests=[82, 170, 43, 140, 24, 16, 190], max_cylinder=199)
        scheduler = DiskScheduler(request)

        fcfs = scheduler.simulate('fcfs')
        sstf = scheduler.simulate('sstf')

        self.assertEqual(fcfs.service_order, [82, 170, 43, 140, 24, 16, 190])
        self.assertEqual(fcfs.total_head_movement, 642)
        self.assertEqual(sstf.service_order, [43, 24, 16, 82, 140, 170, 190])
        self.assertEqual(sstf.total_head_movement, 208)

    def test_scan_and_cscan_capture_boundary_sweeps(self) -> None:
        request = SimulationRequest(start=50, requests=[82, 170, 43, 140, 24, 16, 190], max_cylinder=199, direction='up')
        scheduler = DiskScheduler(request)

        scan = scheduler.simulate('scan')
        cscan = scheduler.simulate('cscan')

        self.assertEqual(scan.service_order, [82, 140, 170, 190, 43, 24, 16])
        self.assertEqual(scan.path, [50, 82, 140, 170, 190, 199, 43, 24, 16])
        self.assertEqual(scan.total_head_movement, 332)

        self.assertEqual(cscan.service_order, [82, 140, 170, 190, 16, 24, 43])
        self.assertEqual(cscan.path, [50, 82, 140, 170, 190, 199, 0, 16, 24, 43])
        self.assertEqual(cscan.total_head_movement, 391)

    def test_look_and_clook_skip_end_cylinder_sweeps(self) -> None:
        request = SimulationRequest(start=50, requests=[82, 170, 43, 140, 24, 16, 190], max_cylinder=199, direction='up')
        scheduler = DiskScheduler(request)

        look = scheduler.simulate('look')
        clook = scheduler.simulate('clook')

        self.assertEqual(look.service_order, [82, 140, 170, 190, 43, 24, 16])
        self.assertEqual(look.path, [50, 82, 140, 170, 190, 43, 24, 16])
        self.assertEqual(look.total_head_movement, 314)

        self.assertEqual(clook.service_order, [82, 140, 170, 190, 16, 24, 43])
        self.assertEqual(clook.path, [50, 82, 140, 170, 190, 16, 24, 43])
        self.assertEqual(clook.total_head_movement, 341)

    def test_downward_variants_handle_missing_lower_half(self) -> None:
        request = SimulationRequest(start=120, requests=[130, 140, 150], max_cylinder=199, direction='down')
        scheduler = DiskScheduler(request)

        scan = scheduler.simulate('scan')
        cscan = scheduler.simulate('cscan')
        look = scheduler.simulate('look')
        clook = scheduler.simulate('clook')

        self.assertEqual(scan.path, [120, 0, 130, 140, 150])
        self.assertEqual(scan.service_order, [130, 140, 150])
        self.assertEqual(cscan.path, [120, 0, 199, 150, 140, 130])
        self.assertEqual(cscan.service_order, [150, 140, 130])

        self.assertEqual(look.path, [120, 130, 140, 150])
        self.assertEqual(look.service_order, [130, 140, 150])
        self.assertEqual(clook.path, [120, 150, 140, 130])
        self.assertEqual(clook.service_order, [150, 140, 130])

    def test_upward_variants_handle_missing_higher_half(self) -> None:
        request = SimulationRequest(start=80, requests=[10, 20, 30], max_cylinder=199, direction='up')
        scheduler = DiskScheduler(request)

        scan = scheduler.simulate('scan')
        cscan = scheduler.simulate('cscan')
        look = scheduler.simulate('look')
        clook = scheduler.simulate('clook')

        self.assertEqual(scan.path, [80, 199, 30, 20, 10])
        self.assertEqual(scan.service_order, [30, 20, 10])
        self.assertEqual(cscan.path, [80, 199, 0, 10, 20, 30])
        self.assertEqual(cscan.service_order, [10, 20, 30])

        self.assertEqual(look.path, [80, 30, 20, 10])
        self.assertEqual(look.service_order, [30, 20, 10])
        self.assertEqual(clook.path, [80, 10, 20, 30])
        self.assertEqual(clook.service_order, [10, 20, 30])

    def test_empty_request_set_stays_at_start(self) -> None:
        request = SimulationRequest(start=50, requests=[], max_cylinder=199, direction='up')
        scheduler = DiskScheduler(request)

        scan = scheduler.simulate('scan')
        cscan = scheduler.simulate('cscan')
        look = scheduler.simulate('look')
        clook = scheduler.simulate('clook')

        self.assertEqual(scan.path, [50])
        self.assertEqual(cscan.path, [50])
        self.assertEqual(look.path, [50])
        self.assertEqual(clook.path, [50])
        self.assertEqual(scan.total_head_movement, 0)
        self.assertEqual(cscan.total_head_movement, 0)
        self.assertEqual(look.total_head_movement, 0)
        self.assertEqual(clook.total_head_movement, 0)

    def test_cli_compare_and_json_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = Path(tmp_dir) / 'requests.json'
            payload.write_text(
                json.dumps({'start': 40, 'max_cylinder': 99, 'direction': 'up', 'requests': [10, 70, 55]}),
                encoding='utf-8',
            )

            request = load_request(payload)
            self.assertEqual(request.requests, [10, 70, 55])

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(['compare', '--input', str(payload), '--algorithms', 'fcfs', 'look', 'clook'])
            self.assertEqual(exit_code, 0)

            output = stdout.getvalue()
            self.assertIn('fcfs', output)
            self.assertIn('look', output)
            self.assertIn('clook', output)
            self.assertIn('total_head_movement', output)


if __name__ == '__main__':
    unittest.main()
