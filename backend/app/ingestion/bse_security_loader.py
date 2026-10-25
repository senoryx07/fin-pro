import sys

from backend.app.providers.bse_security_data import (
    BSESecurityProvider,
)


def load_bse_security_master(
    file_path: str,
) -> None:
    provider = BSESecurityProvider(
        file_path=file_path
    )

    print(
        "Reading BSE security master..."
    )

    securities = provider.get_security_master()

    print()
    print(
        f"BSE equity securities found: "
        f"{len(securities)}"
    )

    print()
    print("First 10 securities:")
    print("----------------------------------------")

    for security in securities[:10]:
        print(
            f"{security['exchange_code']} | "
            f"{security['ticker']} | "
            f"{security['name']} | "
            f"{security['isin']}"
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage:"
        )
        print(
            "python -m backend.app.ingestion."
            "bse_security_loader "
            "<path-to-bse-security-master.csv>"
        )
        raise SystemExit(1)

    load_bse_security_master(
        sys.argv[1]
    )