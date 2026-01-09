from app import create_app

def main() -> None:
    app = create_app()
    # Home Assistant ingress expects add-ons to bind to port 8099 inside the container.
    app.run(host="0.0.0.0", port=8099)

if __name__ == "__main__":
    main()
