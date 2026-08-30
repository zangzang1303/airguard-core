"""Regression contracts for the PlaceSearchOmnibox location-action dropdown."""

from pathlib import Path

FRONTEND_SRC = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
OMNIBOX_FILE = FRONTEND_SRC / "features" / "navigation" / "PlaceSearchOmnibox.tsx"
STYLES_FILE = FRONTEND_SRC / "styles.css"


class TestPlaceSearchOmniboxRegression:
    def setup_method(self):
        self.source = OMNIBOX_FILE.read_text(encoding="utf-8")
        self.styles = STYLES_FILE.read_text(encoding="utf-8")

    def test_rendered_omnibox_classes_have_scoped_styles(self):
        rendered_classes = (
            "search-quick-actions-bar",
            "search-quick-btn",
            "search-dropdown-coord-item",
            "coord-icon",
            "coord-text",
            "item-set-location-btn",
        )
        for class_name in rendered_classes:
            assert class_name in self.source
            assert f".{class_name}" in self.styles

    def test_empty_query_prioritizes_two_location_actions(self):
        assert 'normalizedQuery === ""' in self.source
        assert "Dùng vị trí hiện tại" in self.source
        assert "Chọn trên bản đồ" in self.source
        assert self.source.count('className="search-quick-btn"') == 2
        assert "min-height: 44px;" in self.styles

    def test_interactive_suggestions_use_buttons_without_missing_utilities(self):
        assert 'className="text-primary"' not in self.source
        assert 'className="text-emerald"' not in self.source
        assert 'className="search-dropdown-coord-item"' in self.source
        assert 'className="search-dropdown-ai-item"' in self.source
        assert 'className="search-empty-state"' in self.source
        assert ".search-quick-btn:focus-visible" in self.styles
        assert ".search-dropdown-coord-item:focus-visible" in self.styles
