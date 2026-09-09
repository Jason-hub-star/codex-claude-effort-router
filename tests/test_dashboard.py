from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "index.html"


class DashboardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.disabled_controls = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"button", "select"} and "disabled" in dict(attrs):
            self.disabled_controls += 1


class DashboardTest(unittest.TestCase):
    def test_read_only_routing_studio_contract(self):
        page = DASHBOARD.read_text(encoding="utf-8")
        parser = DashboardParser()
        parser.feed(page)

        self.assertIn("MODEL ORCHESTRATOR", page)
        self.assertIn("ROUTING STUDIO", page)
        self.assertIn("Applies to the next worker or fresh session.", page)
        self.assertIn("SAMPLE RUN · OPENCODE", page)
        self.assertGreaterEqual(parser.disabled_controls, 15)
        self.assertNotRegex(page.lower(), r"purple|violet|lavender|magenta|#7c3aed")


if __name__ == "__main__":
    unittest.main()
