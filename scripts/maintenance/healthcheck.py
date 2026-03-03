from src.dashboard.app import get_dashboard_health


def main() -> None:
    health = get_dashboard_health()
    print(health)


if __name__ == "__main__":
    main()

