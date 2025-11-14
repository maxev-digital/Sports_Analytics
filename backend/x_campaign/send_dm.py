"""
DM Sender
Sends personalized DMs to influencers with rate limiting
"""
import time
import sys
from datetime import datetime
from pathlib import Path

# Handle both direct execution and module import
try:
    from .x_client import get_client
    from .db_setup import mark_dm_sent, get_pending_partners
    from .config import DM_TEMPLATE, DM_DELAY_SECONDS, DAILY_DM_LIMIT
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from x_campaign.x_client import get_client
    from x_campaign.db_setup import mark_dm_sent, get_pending_partners
    from x_campaign.config import DM_TEMPLATE, DM_DELAY_SECONDS, DAILY_DM_LIMIT

def format_dm(handle, followers, why_target):
    """
    Personalize DM template for specific influencer

    Args:
        handle: X handle (e.g., "@BenMoore_Sports")
        followers: Follower count (e.g., 50000)
        why_target: Reason for targeting (e.g., "High NBA engagement")

    Returns:
        str: Personalized DM text
    """
    # Format follower count nicely
    if followers >= 1000000:
        follower_count = f"{followers // 1000000}M"
    elif followers >= 1000:
        follower_count = f"{followers // 1000}K"
    else:
        follower_count = str(followers)

    # Clean handle for display
    clean_handle = handle.replace('@', '')

    return DM_TEMPLATE.format(
        handle=clean_handle,
        follower_count=follower_count,
        why_target=why_target
    )

def send_dm_to_partner(partner_id, handle, followers, why_target, dry_run=False):
    """
    Send DM to a single partner

    Args:
        partner_id: Database ID
        handle: X handle
        followers: Follower count
        why_target: Targeting reason
        dry_run: If True, don't actually send (for testing)

    Returns:
        dict: {success: bool, dm_id: str, error: str}
    """
    # Format message
    message = format_dm(handle, followers, why_target)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN - Would send to @{handle}")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}\n")
        return {
            'success': True,
            'dm_id': 'dry_run_' + str(partner_id),
            'dry_run': True
        }

    # Send via X API
    client = get_client()
    result = client.send_dm(handle, message)

    if result['success']:
        # Update database
        mark_dm_sent(partner_id, result.get('dm_id'))
        print(f"✅ Sent DM to @{handle} (ID: {partner_id})")
    else:
        print(f"❌ Failed to send DM to @{handle}: {result.get('error')}")

    return result

def send_batch(batch_size=50, dry_run=False):
    """
    Send DMs to next batch of partners

    Args:
        batch_size: Number of DMs to send (default 50, max per day)
        dry_run: If True, don't actually send (for testing)

    Returns:
        dict: Stats about send operation
    """
    print(f"\n{'='*60}")
    print(f"Starting DM batch send - {batch_size} DMs")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    # Get pending partners
    partners = get_pending_partners(limit=batch_size)

    if not partners:
        print("[WARN] No pending partners found")
        return {
            'sent': 0,
            'failed': 0,
            'total': 0
        }

    print(f"Found {len(partners)} pending partners")
    print()

    stats = {
        'sent': 0,
        'failed': 0,
        'total': len(partners)
    }

    start_time = datetime.now()

    for idx, (partner_id, handle, followers, niche, why_target) in enumerate(partners, 1):
        print(f"[{idx}/{len(partners)}] Sending to @{handle} ({followers:,} followers)...")

        try:
            result = send_dm_to_partner(
                partner_id=partner_id,
                handle=handle,
                followers=followers,
                why_target=why_target,
                dry_run=dry_run
            )

            if result['success']:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
        except Exception as e:
            print(f"   [ERROR] Exception: {e}")
            stats['failed'] += 1

        # Rate limiting - wait between DMs
        if idx < len(partners) and not dry_run:
            print(f"   Waiting {DM_DELAY_SECONDS}s before next DM...")
            time.sleep(DM_DELAY_SECONDS)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print summary
    print(f"\n{'='*60}")
    print(f"Batch Send Complete")
    print(f"{'='*60}")
    print(f"Total: {stats['total']}")
    print(f"Sent: {stats['sent']} [OK]")
    print(f"Failed: {stats['failed']} [FAIL]")
    print(f"Duration: {duration:.1f}s")
    print(f"{'='*60}\n")

    return stats

if __name__ == "__main__":
    import sys

    # Parse command line args
    dry_run = '--live' not in sys.argv
    batch_size = DAILY_DM_LIMIT

    if '--batch' in sys.argv:
        idx = sys.argv.index('--batch')
        if idx + 1 < len(sys.argv):
            batch_size = int(sys.argv[idx + 1])

    print("DM Sender")
    print("=" * 60)
    print(f"Batch size: {batch_size}")
    print(f"Mode: {'LIVE' if not dry_run else 'DRY RUN'}")
    print()

    if not dry_run:
        confirm = input("[WARN] LIVE MODE - Send real DMs? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            exit(0)

    # Send batch
    send_batch(batch_size=batch_size, dry_run=dry_run)
