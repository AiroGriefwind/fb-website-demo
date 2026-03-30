from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("src.dashboard_api.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

