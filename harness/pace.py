"""Drive a practice clock while a separate live desk plays it."""
import argparse
import signal
import subprocess
import sys
import time

from . import config, slots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', required=True)
    parser.add_argument('--policy', default='main')
    parser.add_argument('--set', action='append', default=[])
    parser.add_argument('--step', type=int, default=5)
    parser.add_argument('--seconds-per-minute', type=float, default=0.3)
    parser.add_argument('--restart', type=int, action='append', default=[])
    parser.add_argument('--real-from', type=int, help='use final speed from this minute')
    parser.add_argument('--end-at', type=int, help='stop the rehearsal at this world minute')
    args = parser.parse_args()
    if not args.seed.startswith('t3-live-') or not args.seed[8:].isdigit():
        parser.error('seed must be t3-live-<n>')
    if args.step < 1 or args.seconds_per_minute < 0:
        parser.error('invalid pace')
    config.load_env()
    client = config.client()
    with slots.create(client, level=8, seed=args.seed) as world:
        command = [sys.executable, '-m', 'dispatch.live', '--world', world.id, '--policy', args.policy]
        for value in args.set:
            command += ['--set', value]
        process = subprocess.Popen(command)
        try:
            time.sleep(3)
            snapshot = world.snapshot()
            now, end = snapshot['now'], min(snapshot['endsAt'], args.end_at or snapshot['endsAt'])
            restarts = sorted(args.restart)
            restart_at = None
            while now < end:
                if restart_at is not None and time.monotonic() >= restart_at:
                    process = subprocess.Popen(command)
                    restart_at = None
                if restart_at is None and process.poll() is not None:
                    raise RuntimeError('live process stopped')
                started = time.monotonic()
                target = min(now + args.step, end)
                duration = (target - now) * (0.3 if restart_at is not None or (args.real_from is not None and now >= args.real_from) else args.seconds_per_minute)
                if restarts and now < restarts[0] <= target:
                    target = restarts[0]
                now = world.advance(to=target)['now']
                if restarts and now >= restarts[0]:
                    restarts.pop(0)
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    restart_at = time.monotonic() + 10
                time.sleep(max(0, duration - (time.monotonic() - started)))
            if end == snapshot['endsAt'] and restart_at is None:
                process.wait(timeout=30)
            print('Score:', world.score(), flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()
