#!/usr/bin/env python3

import argparse
import socket
import sys
from .events_api_v2_client import EventsApiV2Client

HOSTNAME = socket.gethostname()
DEFAULT_SOURCE = f"pagerduty.cli on {HOSTNAME}"

def run(argv):
    parser = argparse.ArgumentParser(
        description='PagerDuty Events API V2 Command Line Interface'
    )
    parser.add_argument('action', choices=['trigger', 'acknowledge', 'resolve'],
        help='Action to perform: trigger, acknowledge, or resolve an incident')
    parser.add_argument('-k', '--routing-key', required=True,
        help='PagerDuty Events API v2 routing key')
    parser.add_argument('-i', '--dedup-key', default=None,
        help='Deduplication key for the incident')
    parser.add_argument('--description', help='Summary/description of the alert')
    parser.add_argument('--source', help='Source of the alert', default=DEFAULT_SOURCE)

    args = parser.parse_args(argv)

    # Create the Events API client
    client = EventsApiV2Client(args.routing_key)

    try:
        # Handle the different actions
        if args.action == 'trigger':
            if not args.description:
                parser.error("--description is required for trigger action")
            dedup_key = client.trigger(args.description, args.source,
                dedup_key=args.dedup_key)
            print(f"Alert triggered successfully. Deduplication key: {dedup_key}")

        elif args.action == 'acknowledge':
            if not args.dedup_key:
                parser.error("-i/--dedup-key is required for acknowledge action")

            dedup_key = client.acknowledge(args.dedup_key)
            print(f"Alert acknowledged successfully. Deduplication key: {dedup_key}")

        elif args.action == 'resolve':
            if not args.dedup_key:
                parser.error("-i/--dedup-key is required for resolve action")

            dedup_key = client.resolve(args.dedup_key)
            print(f"Alert resolved successfully. Deduplication key: {dedup_key}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    run(sys.argv[1:])

if __name__ == '__main__':
    main()
