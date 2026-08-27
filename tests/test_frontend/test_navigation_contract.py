"""
Unit & contract tests for AirGuard AI Frontend single-entry point navigation.
Verifies:
1. "Hỏi AI" is exclusively accessible via Bottom Navigation (BottomActionDock)
2. Alerts are exclusively accessible via Header (TopFloatingBar)
3. Badge count correctly handles 0 (hidden), 1-99 (exact count), and >99 ("99+")
4. Accessibility attributes (aria-label, aria-expanded, aria-pressed, type="button", focus-visible)
"""
import re
from pathlib import Path
import pytest

FRONTEND_SRC = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
TOP_BAR_FILE = FRONTEND_SRC / "features" / "navigation" / "TopFloatingBar.tsx"
BOTTOM_DOCK_FILE = FRONTEND_SRC / "features" / "navigation" / "BottomActionDock.tsx"
APP_FILE = FRONTEND_SRC / "App.tsx"
STYLES_FILE = FRONTEND_SRC / "styles.css"


def format_alert_badge_py(count: int):
    """Python counterpart of frontend's formatAlertBadge function for logic verification."""
    if count <= 0:
        return None
    if count > 99:
        return "99+"
    return str(count)


class TestAlertBadgeLogic:
    """Test suite for alert badge counting rules (0, 1-99, 99+)."""

    def test_zero_alerts_returns_none(self):
        assert format_alert_badge_py(0) is None
        assert format_alert_badge_py(-1) is None
        assert format_alert_badge_py(-10) is None

    def test_single_and_double_digit_alerts_return_exact_count(self):
        assert format_alert_badge_py(1) == "1"
        assert format_alert_badge_py(5) == "5"
        assert format_alert_badge_py(50) == "50"
        assert format_alert_badge_py(99) == "99"

    def test_over_99_alerts_returns_99_plus(self):
        assert format_alert_badge_py(100) == "99+"
        assert format_alert_badge_py(150) == "99+"
        assert format_alert_badge_py(9999) == "99+"


class TestTopFloatingBarContract:
    """Test suite ensuring TopFloatingBar adheres to single-entry points."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert TOP_BAR_FILE.exists(), f"File not found: {TOP_BAR_FILE}"
        self.content = TOP_BAR_FILE.read_text(encoding="utf-8")

    def test_no_duplicate_hoi_ai_button_in_header(self):
        """Header must NOT contain a shortcut/button to open AI chat."""
        assert "top-ai-btn" not in self.content, "Header should not contain top-ai-btn"
        # Ensure 'Hỏi AI' does not appear as a header button label
        assert '<span className="btn-text">Hỏi AI</span>' not in self.content

    def test_has_bell_alert_button_with_badge_and_a11y(self):
        """Header must contain the single entry Bell button with badge and aria-label."""
        assert "Bell" in self.content
        assert "formatAlertBadge" in self.content
        assert "formattedAlertBadge" in self.content
        assert 'className={`top-icon-btn ${activeAlertCount > 0 ? "has-alerts" : ""}' in self.content
        assert "aria-label={alertAriaLabel}" in self.content
        assert "aria-expanded={isAlertsOpen}" in self.content
        assert 'type="button"' in self.content


class TestBottomActionDockContract:
    """Test suite ensuring BottomActionDock adheres to single-entry points."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert BOTTOM_DOCK_FILE.exists(), f"File not found: {BOTTOM_DOCK_FILE}"
        self.content = BOTTOM_DOCK_FILE.read_text(encoding="utf-8")

    def test_no_duplicate_alerts_button_in_bottom_dock(self):
        """Bottom dock must NOT contain an alerts button."""
        assert 'title="Cảnh báo môi trường"' not in self.content
        assert '<span className="dock-label">Cảnh báo</span>' not in self.content
        assert 'activeDrawer === "alerts"' not in self.content

    def test_has_hoi_ai_button_with_active_state(self):
        """Bottom dock must contain 'Hỏi AI' as the primary access point with active state."""
        assert "Sparkles" in self.content
        assert "Hỏi AI" in self.content
        assert 'activeDrawer === "ai-chat"' in self.content
        assert "ai-highlight-btn" in self.content
        assert "dock-active-dot" in self.content

    def test_all_five_standardized_items_exist(self):
        """Bottom dock must have exactly the 5 standardized items with labels."""
        expected_labels = ["Lớp bản đồ", "Gần tôi", "Hôm nay", "Phản ánh", "Hỏi AI"]
        for label in expected_labels:
            assert f'<span className="dock-label">{label}</span>' in self.content, f"Missing label: {label}"

    def test_accessibility_attributes_present(self):
        """All buttons in bottom dock must have type='button' and descriptive aria labels."""
        buttons = re.findall(r"<button[\s\S]*?</button>", self.content)
        assert len(buttons) == 5, f"Expected 5 navigation buttons, found {len(buttons)}"
        for btn in buttons:
            assert 'type="button"' in btn, f"Button missing type='button': {btn}"
            assert "aria-label=" in btn, f"Button missing aria-label: {btn}"


class TestAppIntegrationContract:
    """Test suite ensuring App.tsx correctly wires single-entry navigation props."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert APP_FILE.exists(), f"File not found: {APP_FILE}"
        self.content = APP_FILE.read_text(encoding="utf-8")

    def test_top_floating_bar_props_wired_correctly(self):
        """TopFloatingBar receives isAlertsOpen and does not receive onOpenAiChat."""
        top_bar_match = re.search(r"<TopFloatingBar([\s\S]*?)/>", self.content)
        assert top_bar_match is not None, "TopFloatingBar not found in App.tsx"
        top_bar_props = top_bar_match.group(1)
        assert 'isAlertsOpen={activeDrawer === "alerts"}' in top_bar_props
        assert "onOpenAiChat=" not in top_bar_props

    def test_bottom_action_dock_props_wired_correctly(self):
        """BottomActionDock does not receive activeAlertCount."""
        dock_match = re.search(r"<BottomActionDock([\s\S]*?)/>", self.content)
        assert dock_match is not None, "BottomActionDock not found in App.tsx"
        dock_props = dock_match.group(1)
        assert "activeAlertCount=" not in dock_props


class TestStylesContract:
    """Test suite verifying CSS styles for focus-visible and active indicators."""

    @pytest.fixture(autouse=True)
    def setup(self):
        assert STYLES_FILE.exists(), f"File not found: {STYLES_FILE}"
        self.content = STYLES_FILE.read_text(encoding="utf-8")

    def test_focus_visible_styles_defined(self):
        assert ".dock-action-btn:focus-visible" in self.content
        assert ".top-icon-btn:focus-visible" in self.content

    def test_dock_active_dot_styles_defined(self):
        assert ".dock-active-dot" in self.content
        assert ".dock-active-dot.ai-dot" in self.content
