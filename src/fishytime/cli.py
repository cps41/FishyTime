import argparse
from datetime import date, datetime, timezone

from fishytime.pipeline import run_pipeline


def _print_report(results, target_date: date) -> None:
    print(f"FishyTime report for {target_date.isoformat()}\n")
    for rank, result in enumerate(results, start=1):
        print(f"{rank}. {result.water_name} — score {result.total_score:+.2f}")
        for factor in result.factors:
            flag = " (missing)" if factor.missing else ""
            print(f"     {factor.name}: {factor.reason}{flag}")
        if result.caveats:
            print("     Caveats:")
            for caveat in result.caveats:
                print(f"       - {caveat}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank Colorado Front Range trout waters for a given date.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(timezone.utc).date(),
        help="Target date in YYYY-MM-DD format (default: today, UTC).",
    )
    args = parser.parse_args()

    results = run_pipeline(args.date)
    _print_report(results, args.date)


if __name__ == "__main__":
    main()
