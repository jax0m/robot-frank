from flask import Flask, render_template, jsonify
import threading


class WebServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.running = False
        self.server_thread = None

        # Initialize all hardware components
        # These will be initialized when the server starts

    def start(self):
        """Start the web server"""
        if not self.running:
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            print("Web server started on http://localhost:5000")
        else:
            print("Web server is already running")

    def stop(self):
        """Stop the web server"""
        if self.running:
            self.running = False
            if self.server_thread:
                self.server_thread.join()
            print("Web server stopped")

    def _run_server(self):
        """Internal method to run the Flask server"""
        if self.running:
            # Set up routes
            @self.app.route("/")
            def index():
                return render_template("index.html")

            @self.app.route("/api/camera")
            def camera():
                # Return camera info
                return jsonify({"status": "OK", "message": "Camera accessed"})

            @self.app.route("/api/motors")
            def motors():
                # Return motors info
                return jsonify({"status": "OK", "message": "Motors accessed"})

            @self.app.route("/api/leds")
            def leds():
                # Return LEDs info
                return jsonify({"status": "OK", "message": "LEDs accessed"})

            @self.app.route("/api/ultrasonic")
            def ultrasonic():
                # Return ultrasonic sensor info
                return jsonify(
                    {"status": "OK", "message": "Ultrasonic sensor accessed"}
                )

            # Run the server
            self.app.run(host="0.0.0.0.0", port=5000, debug=False)

    def get_status(self):
        """Get the current status of the web server"""
        return {
            "running": self.running,
            "host": "0.0.0.0",
            "port": 5000,
            "url": "http://localhost:5000",
        }
