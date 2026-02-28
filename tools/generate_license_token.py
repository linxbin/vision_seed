import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.license_manager import LicenseManager


def main():
    parser = argparse.ArgumentParser(description="Generate VisionSeed device-bound activation token.")
    parser.add_argument("--license-id", required=True, help="Unique license id, e.g. LIC_20260228_0001")
    parser.add_argument("--order-ref", required=True, help="Order reference, e.g. XIAN_YU_123456")
    parser.add_argument("--device-hash", required=True, help="Target device hash from client")
    parser.add_argument("--expires-at", default=None, help="Optional ISO UTC timestamp, e.g. 2026-12-31T23:59:59Z")
    args = parser.parse_args()

    token = LicenseManager.create_activation_token(
        license_id=args.license_id.strip(),
        order_ref=args.order_ref.strip(),
        device_hash=args.device_hash.strip(),
        expires_at=args.expires_at.strip() if args.expires_at else None,
    )

    output = {
        "license_id": args.license_id,
        "order_ref": args.order_ref,
        "device_hash": args.device_hash,
        "expires_at": args.expires_at,
        "token": token,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
