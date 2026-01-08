"""WSGI entrypoint for HomeOps Doctor.

When executed directly, this module will construct the Flask
application using the factory defined in :mod:`app.__init__` and
serve it on port 8099.  This port is fixed because Home Assistant
expects ingress add‑ons to bind to port 8099 inside the container.

Note that this uses Flask’s built‑in development server.  In
production environments you may wish to run under a WSGI server
such as Gunicorn, but for Home Assistant add‑ons the development
server is sufficient.
"""

# Import the create_app factory from the package.  Use an absolute
# import here rather than a relative one so that the module can be
# executed directly as a script ("python app/main.py").  When run as
# a script, Python sets __package__ to None and relative imports fail.
from app import create_app


def main() -> None:
    """Run the Flask application if executed as a script."""
    app = create_app()
    # Bind to all addresses on the reserved ingress port (8099)
    app.run(host="0.0.0.0", port=8099)


if __name__ == "__main__":
    main()