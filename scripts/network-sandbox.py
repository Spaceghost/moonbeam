#!/usr/bin/env python3
"""Run a test client with private, bidirectional loss/jitter/outages on Linux.

Only the child network namespace is modified. The host interfaces, host game,
and other clients are unaffected. Run --self-test before testing a stream.
"""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def impairment(device, config, outage=False):
    args = ['tc', 'qdisc', 'replace', 'dev', device, 'root', 'netem', 'limit', '1000']
    if config['delay_ms']:
        args += ['delay', f"{config['delay_ms']}ms", f"{config['jitter_ms']}ms"]
    args += ['loss', f"{100 if outage else config['loss_percent']}%"]
    run(*args)


def worker(config_path):
    config = json.loads(config_path.read_text())
    config_path.with_suffix('.pid').write_text(str(os.getpid()))
    ready = config_path.with_suffix('.ready')
    while not ready.exists():
        time.sleep(0.02)
    run('ip', 'link', 'add', 'moonbeam-ifb', 'type', 'ifb')
    run('ip', 'link', 'set', 'moonbeam-ifb', 'up')
    run('tc', 'qdisc', 'add', 'dev', 'tap0', 'handle', 'ffff:', 'ingress')
    run('tc', 'filter', 'add', 'dev', 'tap0', 'parent', 'ffff:', 'protocol', 'all',
        'u32', 'match', 'u32', '0', '0', 'action', 'mirred', 'egress', 'redirect', 'dev', 'moonbeam-ifb')
    for device in ['tap0', 'moonbeam-ifb']:
        impairment(device, config)
    if config['self_test']:
        samples = []
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.settimeout(0.25 + config['delay_ms'] / 250)
            for index in range(60):
                start = time.monotonic()
                payload = str(index).encode()
                probe.sendto(payload, ('10.0.2.2', config['echo_port']))
                try:
                    while probe.recv(64) != payload:
                        pass
                    samples.append((time.monotonic() - start) * 1000)
                except socket.timeout:
                    pass
        print(json.dumps({'sent': 60, 'received': len(samples), 'lost': 60-len(samples),
                          'median_rtt_ms': round(statistics.median(samples), 2) if samples else None}), flush=True)
        return 0 if samples else 1

    command = config['command']
    child = subprocess.Popen(command)
    stopping = False
    def stop(_signal, _frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    start = time.monotonic()
    in_outage = False
    try:
        while child.poll() is None and not stopping:
            elapsed = time.monotonic() - start
            if elapsed >= config['duration']:
                break
            outage = (config['outage_after'] > 0 and
                      config['outage_after'] <= elapsed < config['outage_after'] + config['outage_seconds'])
            if outage != in_outage:
                for device in ['tap0', 'moonbeam-ifb']:
                    impairment(device, config, outage)
                print('NETWORK_OUTAGE_STARTED' if outage else 'NETWORK_RESTORED', flush=True)
                in_outage = outage
            time.sleep(0.05)
        return child.returncode if child.returncode is not None else 0
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        return worker(Path(sys.argv[2]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delay-ms', type=float, default=0)
    parser.add_argument('--jitter-ms', type=float, default=0)
    parser.add_argument('--loss-percent', type=float, default=0)
    parser.add_argument('--duration', type=float, default=60)
    parser.add_argument('--outage-after', type=float, default=0)
    parser.add_argument('--outage-seconds', type=float, default=12)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not (0 <= args.jitter_ms <= args.delay_ms <= 1000 and 0 <= args.loss_percent <= 100):
        parser.error('Require 0 <= jitter <= delay <= 1000 ms and 0 <= loss <= 100%.')
    if not (0 < args.duration <= 3600 and 0 <= args.outage_after < args.duration and 0 < args.outage_seconds <= 300):
        parser.error('Invalid duration or outage window.')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not args.self_test and not command:
        parser.error('Provide --self-test or a client command after --.')
    if command:
        if any(arg.lstrip('-').split('=')[0] == 'quit-after' for arg in command):
            parser.error('Stream tests must keep the host game running; remove --quit-after.')
        if 'stream' in command and '--no-quit-after' not in command:
            command.append('--no-quit-after')
        executable = shutil.which(command[0])
        if not executable:
            parser.error('Client executable was not found.')
        command[0] = executable
    for tool in ['unshare', 'slirp4netns', 'ip', 'tc']:
        if not shutil.which(tool):
            parser.error(f'Missing required tool: {tool}')
    with tempfile.TemporaryDirectory(prefix='moonbeam-network-') as directory:
        config_path = Path(directory) / 'config.json'
        config = vars(args) | {'command': command}
        echo = None
        if args.self_test:
            echo = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            echo.bind(('127.0.0.1', 0))
            config['echo_port'] = echo.getsockname()[1]
            def echo_loop():
                while True:
                    try:
                        data, peer = echo.recvfrom(64)
                        echo.sendto(data, peer)
                    except OSError:
                        return
            threading.Thread(target=echo_loop, daemon=True).start()
        config_path.write_text(json.dumps(config))
        config_path.chmod(0o600)
        process = subprocess.Popen(['unshare', '--user', '--map-root-user', '--net',
                                    sys.executable, str(Path(__file__).resolve()), '--worker', str(config_path)])
        network = None
        read_fd, write_fd = os.pipe()
        try:
            deadline = time.monotonic() + 15
            while not config_path.with_suffix('.pid').exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('Could not create a private network namespace.')
                time.sleep(0.02)
            pid = config_path.with_suffix('.pid').read_text()
            network = subprocess.Popen(['slirp4netns', '--configure', '--mtu=1500',
                                        f'--ready-fd={write_fd}', pid, 'tap0'], pass_fds=(write_fd,),
                                       stdout=subprocess.DEVNULL)
            os.close(write_fd)
            write_fd = None
            if not select.select([read_fd], [], [], 15)[0] or not os.read(read_fd, 1):
                raise RuntimeError('Private network setup failed.')
            config_path.with_suffix('.ready').touch()
            return process.wait(timeout=(90 if args.self_test else args.duration + 30))
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if network is not None:
                network.terminate()
                network.wait(timeout=10)
            os.close(read_fd)
            if write_fd is not None:
                os.close(write_fd)
            if echo is not None:
                echo.close()


if __name__ == '__main__':
    sys.exit(main())
