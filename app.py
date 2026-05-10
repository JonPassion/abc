"""
Fallback WSGI application for Render deployment.
This file exists to handle cases where Render tries to import 'app' module.
"""

from datingsite.wsgi import application

# Expose the WSGI application
if __name__ == "__main__":
    # This allows running the app directly for testing
    from wsgiref.simple_server import make_server
    import os
    port = int(os.environ.get('PORT', 8000))
    make_server('', port, application)
