"""
Main application module
"""


class App:
    """Main application class"""

    def __init__(self):
        """Initialize the app"""
        self.config = {}

    def run(self):
        """Run the application"""
        print("FureverMatch App is running...")

    def __call__(self):
        """Make the app callable"""
        self.run()


def main():
    """Entry point for the application"""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
