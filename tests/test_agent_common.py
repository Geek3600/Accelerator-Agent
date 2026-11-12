import os
import sys
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.agent_common import ToolRunner


class ToolRunnerMemoryGuardTest(TestCase):
    def setUp(self) -> None:
        cache = TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        settings = patch.dict(os.environ, {
            "XDG_CACHE_HOME": cache.name, "SPATIALACC_DEBUG_LOOP_SLOTS": "1",
        })
        settings.start()
        self.addCleanup(settings.stop)

    def test_bounded_parallel_slots_allow_two_workers_and_block_a_third(self) -> None:
        if sys.platform != "linux":
            self.skipTest("Stage-6 slot locks are Linux-specific")
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = []
            maximum = []
            mutex = threading.Lock()
            entered_two = threading.Event()
            release = threading.Event()
            settings = {"SPATIALACC_DEBUG_LOOP_SLOTS": "2", "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "64"}

            def worker() -> None:
                runner = ToolRunner(root, root / "logs")
                with runner._debug_loop_memory_slot(settings):
                    with mutex:
                        active.append(threading.get_ident())
                        maximum.append(len(active))
                        if len(active) == 2:
                            entered_two.set()
                    release.wait(3)
                    with mutex:
                        active.remove(threading.get_ident())

            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(root / "cache")}), patch.object(
                ToolRunner, "_available_memory_kib", return_value=16 * 1024 * 1024
            ):
                workers = [threading.Thread(target=worker) for _ in range(3)]
                for task in workers:
                    task.start()
                try:
                    self.assertTrue(entered_two.wait(2))
                    self.assertEqual(max(maximum), 2)
                finally:
                    release.set()
                    for task in workers:
                        task.join(4)
                self.assertTrue(all(not task.is_alive() for task in workers))
                self.assertEqual(max(maximum), 2)

    def test_parallel_slot_waits_for_memory_and_preserves_legacy_exclusive_lock(self) -> None:
        if sys.platform != "linux":
            self.skipTest("Stage-6 slot locks are Linux-specific")
        import fcntl

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock_dir = root / "cache" / "spatialaccagent"
            lock_dir.mkdir(parents=True)
            with (lock_dir / "debug_loop.lock").open("a") as legacy:
                fcntl.flock(legacy.fileno(), fcntl.LOCK_EX)
                runner = ToolRunner(root, root / "logs")
                settings = {"SPATIALACC_DEBUG_LOOP_SLOTS": "2", "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "64"}
                with patch.dict(os.environ, {"XDG_CACHE_HOME": str(root / "cache")}), patch.object(
                    ToolRunner, "_available_memory_kib", side_effect=[0, 16 * 1024 * 1024]
                ) as available, patch("accagent.framework.agent_common.time.sleep") as sleep:
                    with runner._debug_loop_memory_slot(settings):
                        self.assertEqual(available.call_count, 2)
                        sleep.assert_called_once()
                        with (lock_dir / "debug_loop.1.lock").open("a") as other:
                            with self.assertRaises(BlockingIOError):
                                fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_parallel_slots_reject_an_unbounded_worker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(root / "cache")}):
                with self.assertRaisesRegex(ValueError, "require a process-group RSS limit"):
                    with runner._debug_loop_memory_slot({
                        "SPATIALACC_DEBUG_LOOP_SLOTS": "2", "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "0",
                    }):
                        self.fail("unbounded worker admitted")

    def test_parallel_worker_stops_if_system_memory_reserve_is_exhausted(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            with patch.object(ToolRunner, "_available_memory_kib", side_effect=[16 * 1024 * 1024, 1024]):
                result = runner.run("debug_loop", [sys.executable, "-c", "import time; time.sleep(5)"], env={
                    "SPATIALACC_DEBUG_LOOP_SLOTS": "2", "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "64",
                })
            self.assertEqual(result.returncode, 125)
            self.assertIn("system available memory fell below the Stage-6 reserve", result.stdout)

    def test_debug_loop_rss_limit_stops_only_the_worker_process_group(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            started = time.monotonic()
            result = runner.run(
                "debug_loop",
                [
                    sys.executable,
                    "-c",
                    "import time; allocation = bytearray(256 * 1024 * 1024); time.sleep(5)",
                ],
                env={"SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "96"},
            )

            self.assertEqual(result.returncode, 125)
            self.assertIn("exceeded its local process-group RSS limit", result.stdout)
            self.assertLess(time.monotonic() - started, 5)

    def test_debug_loop_address_space_limit_is_applied_before_worker_exec(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            result = runner.run(
                "debug_loop",
                [
                    sys.executable,
                    "-c",
                    "import resource; print(resource.getrlimit(resource.RLIMIT_AS)[0])",
                ],
                env={
                    "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "0",
                    "SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB": "256",
                },
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(int(result.stdout.strip()), 256 * 1024 * 1024)

    def test_address_space_limit_blocks_large_allocation_without_killing_wsl(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            result = runner.run(
                "debug_loop",
                [
                    sys.executable,
                    "-c",
                    "try:\n"
                    " bytearray(512 * 1024 * 1024)\n"
                    "except MemoryError:\n"
                    " print('allocation blocked by process limit')",
                ],
                env={
                    "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "0",
                    "SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB": "256",
                },
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("allocation blocked by process limit", result.stdout)

    def test_debug_loop_stdout_is_saved_and_bounded_in_memory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            expected_size = 2 * 1024 * 1024
            with open(os.devnull, "w", encoding="utf-8") as quiet_stderr:
                with patch("sys.stderr", quiet_stderr):
                    result = runner.run(
                        "debug_loop",
                        [
                            sys.executable,
                            "-c",
                            f"import sys; sys.stdout.write('x' * {expected_size})",
                        ],
                        env={"SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "0"},
                    )

            self.assertEqual(result.returncode, 0)
            self.assertTrue(result.stdout_truncated)
            self.assertLessEqual(
                len(result.stdout.encode("utf-8")),
                ToolRunner.DEBUG_LOOP_MAX_CAPTURE_BYTES + 200,
            )
            self.assertEqual(Path(result.stdout_artifact_path).stat().st_size, expected_size)

    def test_memory_guard_kills_group_children_that_ignore_sigterm(self) -> None:
        if sys.platform != "linux":
            self.skipTest("process-group memory guard is Linux-specific")
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pid_path = root / "child.pid"
            runner = ToolRunner(root, root / "logs")
            command = (
                "import signal, subprocess, sys, time; "
                "child = subprocess.Popen([sys.executable, '-c', "
                "\"import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(15)\"]); "
                f"open({str(pid_path)!r}, 'w').write(str(child.pid)); "
                "allocation = bytearray(256 * 1024 * 1024); time.sleep(15)"
            )
            result = runner.run(
                "debug_loop",
                [sys.executable, "-c", command],
                env={
                    "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "96",
                    "SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB": "0",
                },
            )

            self.assertEqual(result.returncode, 125)
            child_pid = int(pid_path.read_text(encoding="ascii"))
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and Path(f"/proc/{child_pid}").exists():
                try:
                    stat_path = Path(f"/proc/{child_pid}/stat")
                    stat = stat_path.read_text(encoding="ascii")
                except FileNotFoundError:
                    break
                if stat[stat.rfind(")") + 2 :].split()[0] == "Z":
                    break
                time.sleep(0.05)
            child_stat_path = Path(f"/proc/{child_pid}/stat")
            child_is_running = False
            if child_stat_path.exists():
                stat = child_stat_path.read_text(encoding="ascii")
                child_is_running = stat[stat.rfind(")") + 2 :].split()[0] != "Z"
            self.assertFalse(
                child_is_running,
                "RSS guard left a live child process in the worker group",
            )

    def test_debug_loop_runs_are_serialized_across_agent_instances(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            events_path = root / "events.log"
            errors = []

            def run_worker() -> None:
                runner = ToolRunner(root, root / "logs" / str(threading.get_ident()))
                code = (
                    "import time; "
                    f"p = {str(events_path)!r}; "
                    "open(p, 'a').write('start\\n'); time.sleep(0.2); "
                    "open(p, 'a').write('end\\n')"
                )
                result = runner.run(
                    "debug_loop",
                    [sys.executable, "-c", code],
                    env={
                        "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "0",
                        "SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB": "0",
                    },
                )
                if not result.passed:
                    errors.append(result.stdout)

            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(root / "cache")}):
                workers = [threading.Thread(target=run_worker) for _ in range(2)]
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join(timeout=5)

            self.assertTrue(all(not worker.is_alive() for worker in workers))
            self.assertEqual(errors, [])
            self.assertEqual(
                events_path.read_text(encoding="ascii").splitlines(),
                ["start", "end", "start", "end"],
            )

    def test_non_debug_tools_do_not_get_the_stage6_rss_limit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = ToolRunner(root, root / "logs")
            result = runner.run(
                "small_tool",
                [sys.executable, "-c", "print('ok')"],
                env={"SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "1"},
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("ok", result.stdout)
