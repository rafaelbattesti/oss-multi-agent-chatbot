import uvicorn

from bastion.server import app


def main() -> None:
  uvicorn.run(app, host="127.0.0.1", port=9999)


if __name__ == "__main__":
  main()
