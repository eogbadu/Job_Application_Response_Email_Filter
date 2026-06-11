import sys
from app.config import load_config
from app.classifier import classify
from app.imap_client import ImapEmailClient
from app.storage import load_processed_message_ids, save_processed_message_ids


def run() -> None:
    try:
        config = load_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    print(f"Provider: {config.provider}")
    print(f"Email: {config.email_address}")
    print(f"Target folder: {config.target_folder}")
    print(f"Dry run: {config.dry_run}")

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
                print(f"[ERROR] Could not fetch UID {mid!r}: {exc}")
                continue

            if parsed.uid in processed_ids:
                continue

            result = classify(parsed.sender, parsed.subject, parsed.body)

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
                        continue
            else:
                print(f"[SKIP] {parsed.subject} | {parsed.sender}")
                print(f"Reason: {result.reason}\n")

            newly_processed.add(parsed.uid)

        save_processed_message_ids(processed_ids | newly_processed)

    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    run()
