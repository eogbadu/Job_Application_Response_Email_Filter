import sys
import time
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from app.config import load_config
from app.classifier import classify
from app.imap_client import ImapEmailClient
from app.storage import load_processed_message_ids, save_processed_message_ids
from app.applied_jobs import load_applied_companies, create_template
from app.blocklist import load_sender_blocklist, add_to_blocklist


@dataclass
class ScanStats:
    matched: int = 0
    skipped: int = 0
    blocked: int = 0
    already_processed: int = 0
    errors: int = 0

    @property
    def total(self) -> int:
        return self.matched + self.skipped + self.blocked + self.errors


def _print_summary(stats: ScanStats) -> None:
    print("─" * 50)
    print(
        f"Summary  matched={stats.matched}  skipped={stats.skipped}"
        f"  blocked={stats.blocked}  errors={stats.errors}"
        f"  already-processed={stats.already_processed}"
    )
    print("─" * 50)


def _scan(config, applied_companies: list[str], sender_blocklist: list[str]) -> ScanStats:
    stats = ScanStats()
    processed_ids = load_processed_message_ids()

    client = ImapEmailClient(
        host=config.imap_host,
        email_address=config.email_address,
        app_password=config.app_password,
    )

    try:
        client.connect()
        client.ensure_folder_exists(config.target_folder)
        client.select_inbox()

        message_ids = client.search_recent_messages(config.max_messages)
        print(f"Found {len(message_ids)} unread message(s).\n")

        newly_processed: set[str] = set()

        for mid in message_ids:
            try:
                parsed = client.fetch_message(mid)
            except Exception as exc:
                print(f"[ERROR] Could not fetch UID {mid!r}: {exc}\n")
                stats.errors += 1
                continue

            if parsed.uid in processed_ids:
                stats.already_processed += 1
                continue

            result = classify(
                parsed.sender,
                parsed.subject,
                parsed.body,
                applied_companies,
                sender_blocklist,
            )

            if result.matched:
                print(f"[MATCH] {parsed.subject} | {parsed.sender}")
                print(f"Reason: {result.reason}")
                if config.dry_run:
                    print(f"Action: would move to {config.target_folder}\n")
                else:
                    try:
                        client.move_message(mid, config.target_folder)
                        print(f"Action: moved to {config.target_folder}\n")
                    except Exception as exc:
                        print(f"Action: move failed — {exc}\n")
                        stats.errors += 1
                        continue
                stats.matched += 1
            elif "blocklist" in result.reason:
                print(f"[BLOCK] {parsed.subject} | {parsed.sender}")
                stats.blocked += 1
            else:
                print(f"[SKIP] {parsed.subject} | {parsed.sender}")
                print(f"Reason: {result.reason}\n")
                stats.skipped += 1

            newly_processed.add(parsed.uid)

        save_processed_message_ids(processed_ids | newly_processed)

    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    finally:
        client.close()

    return stats


def run() -> None:
    parser = argparse.ArgumentParser(description="Job application email sorter")
    parser.add_argument(
        "--block",
        metavar="SENDER",
        help="Add a sender to the blocklist and exit (e.g. --block 'noreply@example.com')",
    )
    parser.add_argument(
        "--watch",
        metavar="MINUTES",
        type=int,
        help="Re-run every N minutes until Ctrl+C (e.g. --watch 15)",
    )
    args = parser.parse_args()

    try:
        config = load_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    if args.block:
        add_to_blocklist(config.sender_blocklist_file, args.block)
        return

    if not Path(config.applied_jobs_file).exists():
        create_template(config.applied_jobs_file)
        print(f"Created blank applied-jobs template: {config.applied_jobs_file}")

    applied_companies = load_applied_companies(config.applied_jobs_file)
    sender_blocklist = load_sender_blocklist(config.sender_blocklist_file)

    print(f"Provider:        {config.provider}")
    print(f"Email:           {config.email_address}")
    print(f"Target folder:   {config.target_folder}")
    print(f"Dry run:         {config.dry_run}")
    print(f"Applied jobs:    {config.applied_jobs_file} ({len(applied_companies)} companies)")
    print(f"Sender blocklist:{config.sender_blocklist_file} ({len(sender_blocklist)} entries)")
    if args.watch:
        print(f"Watch mode:      every {args.watch} minute(s)\n")

    if args.watch:
        try:
            run_number = 1
            while True:
                print(f"\n{'═' * 50}")
                print(f"  Run #{run_number}")
                print(f"{'═' * 50}\n")
                stats = _scan(config, applied_companies, sender_blocklist)
                _print_summary(stats)
                print(f"\nNext scan in {args.watch} minute(s) — Ctrl+C to stop.\n")
                time.sleep(args.watch * 60)
                run_number += 1
        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
    else:
        print()
        stats = _scan(config, applied_companies, sender_blocklist)
        _print_summary(stats)


if __name__ == "__main__":
    run()
