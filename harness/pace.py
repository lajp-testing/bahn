"""Drive a practice clock while a separate live desk plays it."""
import argparse
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
            now, end = snapshot['now'], snapshot['endsAt']
            while now < end:
                if process.poll() is not None:
                    raise RuntimeError('live process stopped')
                started = time.monotonic()
                target = min(now + args.step, end)
                duration = (target - now) * args.seconds_per_minute
                now = world.advance(to=target)['now']
                time.sleep(max(0, duration - (time.monotonic() - started)))
            process.wait(timeout=30)
            print('Score:', world.score(), flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()


if __name__ == '__main__':
    main()
