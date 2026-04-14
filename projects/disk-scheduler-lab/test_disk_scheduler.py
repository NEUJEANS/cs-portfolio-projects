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

    def test_downward_scan_handles_empty_initial_half(self) -> None:
        request = SimulationRequest(start=120, requests=[130, 140, 150], max_cylinder=199, direction='down')
        scheduler = DiskScheduler(request)

        scan = scheduler.simulate('scan')
        cscan = scheduler.simulate('cscan')

        self.assertEqual(scan.path, [120, 0, 130, 140, 150])
        self.assertEqual(scan.service_order, [130, 140, 150])
        self.assertEqual(cscan.path, [120, 0, 199, 150, 140, 130])
        self.assertEqual(cscan.service_order, [150, 140, 130])

    def test_empty_request_set_stays_at_start(self) -> None:
        request = SimulationRequest(start=50, requests=[], max_cylinder=199, direction='up')
        scheduler = DiskScheduler(request)

        scan = scheduler.simulate('scan')
        cscan = scheduler.simulate('cscan')

        self.assertEqual(scan.path, [50])
        self.assertEqual(cscan.path, [50])
        self.assertEqual(scan.total_head_movement, 0)
        self.assertEqual(cscan.total_head_movement, 0)

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
                exit_code = main(['--input', str(payload), 'compare', '--algorithms', 'fcfs', 'sstf'])
            self.assertEqual(exit_code, 0)

            output = stdout.getvalue()
            self.assertIn('fcfs', output)
            self.assertIn('sstf', output)
            self.assertIn('total_head_movement', output)


if __name__ == '__main__':
    unittest.main()
