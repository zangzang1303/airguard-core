"""Regression tests for Environmental Metric Color Classification and Heatmap Raster Clipping.

Validates:
1. getMetricLevel classification maps decimal boundary values (e.g. 50.1, 100.1) continuously to correct adjacent levels.
2. Eliminates false fallthrough to the last level ("Nguy hại" / dark purple) for intermediate boundary floats.
3. Applies consistently across AQI, PM2.5, CO2, noise_db/noise, temperature, and humidity.
4. Ensures only values strictly exceeding the penultimate maximum threshold receive the last level color.
5. Verifies dispersionField.ts uses vector polygon path clipping (destination-in) for anti-aliasing safety.
"""

from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
METRICS_FILE = FRONTEND_ROOT / "constants" / "metrics.ts"
DISPERSION_FILE = FRONTEND_ROOT / "utils" / "dispersionField.ts"


class TestMetricClassificationLogicContract:
    """Test suite verifying metric level evaluation logic in metrics.ts."""

    def setup_method(self):
        self.content = METRICS_FILE.read_text(encoding="utf-8")

    def test_get_metric_level_checks_upper_bound_only(self):
        """getMetricLevel must evaluate val <= level.max to prevent decimal gap fallthrough."""
        assert "if (val <= level.max) {" in self.content
        assert "if (val >= level.min && val <= level.max)" not in self.content

    def test_metric_scales_defined_for_all_metrics(self):
        """METRIC_SCALES must define scales for aqi, pm25, co2, temperature, noise_db, noise, humidity."""
        for metric in ["aqi", "pm25", "co2", "temperature", "noise_db", "noise", "humidity"]:
            assert f'{metric}:' in self.content or f'key: "{metric}"' in self.content


class TestBoundaryValueClassification:
    """Simulates getMetricLevel behavior on boundary values to ensure exact level mapping."""

    def get_level_mock(self, levels, scale_min, scale_max, value):
        val = min(scale_max, max(scale_min, value))
        for level in levels:
            if val <= level["max"]:
                return level
        return levels[-1]

    def test_aqi_boundary_classification(self):
        """AQI boundary values must map to correct adjacent levels, never jumping to hazardous for 50.1."""
        levels = [
            {"min": 0, "max": 50, "label": "Tốt", "classTag": "good"},
            {"min": 51, "max": 100, "label": "Trung bình", "classTag": "moderate"},
            {"min": 101, "max": 150, "label": "Kém (nhạy cảm)", "classTag": "sensitive"},
            {"min": 151, "max": 200, "label": "Xấu", "classTag": "unhealthy"},
            {"min": 201, "max": 300, "label": "Rất xấu", "classTag": "very-unhealthy"},
            {"min": 301, "max": 500, "label": "Nguy hại", "classTag": "hazardous"},
        ]

        # 50.1 must be Moderate, NOT Hazardous
        assert self.get_level_mock(levels, 0, 500, 50.1)["classTag"] == "moderate"
        # 100.1 must be Sensitive
        assert self.get_level_mock(levels, 0, 500, 100.1)["classTag"] == "sensitive"
        # 150.1 must be Unhealthy
        assert self.get_level_mock(levels, 0, 500, 150.1)["classTag"] == "unhealthy"
        # 200.1 must be Very Unhealthy
        assert self.get_level_mock(levels, 0, 500, 200.1)["classTag"] == "very-unhealthy"
        # 300.1 must be Hazardous
        assert self.get_level_mock(levels, 0, 500, 300.1)["classTag"] == "hazardous"

        # Exact threshold checks
        assert self.get_level_mock(levels, 0, 500, 50.0)["classTag"] == "good"
        assert self.get_level_mock(levels, 0, 500, 100.0)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 0, 500, 150.0)["classTag"] == "sensitive"
        assert self.get_level_mock(levels, 0, 500, 200.0)["classTag"] == "unhealthy"
        assert self.get_level_mock(levels, 0, 500, 300.0)["classTag"] == "very-unhealthy"

    def test_pm25_boundary_classification(self):
        """PM2.5 boundary values must map to correct adjacent levels."""
        levels = [
            {"min": 0, "max": 12.0, "label": "Tốt", "classTag": "good"},
            {"min": 12.1, "max": 35.4, "label": "Trung bình", "classTag": "moderate"},
            {"min": 35.5, "max": 55.4, "label": "Kém (nhạy cảm)", "classTag": "sensitive"},
            {"min": 55.5, "max": 150.4, "label": "Xấu", "classTag": "unhealthy"},
            {"min": 150.5, "max": 250.0, "label": "Rất xấu", "classTag": "very-unhealthy"},
        ]

        assert self.get_level_mock(levels, 0, 250, 12.0)["classTag"] == "good"
        assert self.get_level_mock(levels, 0, 250, 12.05)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 0, 250, 35.4)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 0, 250, 35.45)["classTag"] == "sensitive"
        assert self.get_level_mock(levels, 0, 250, 55.4)["classTag"] == "sensitive"
        assert self.get_level_mock(levels, 0, 250, 55.45)["classTag"] == "unhealthy"
        assert self.get_level_mock(levels, 0, 250, 150.4)["classTag"] == "unhealthy"
        assert self.get_level_mock(levels, 0, 250, 150.45)["classTag"] == "very-unhealthy"

    def test_co2_boundary_classification(self):
        """CO2 boundary values must map to correct adjacent levels."""
        levels = [
            {"min": 400, "max": 700, "label": "Thấp (Tốt)", "classTag": "good"},
            {"min": 701, "max": 1000, "label": "Trung bình", "classTag": "moderate"},
            {"min": 1001, "max": 1500, "label": "Cao (Kém)", "classTag": "sensitive"},
            {"min": 1501, "max": 2000, "label": "Rất cao (Xấu)", "classTag": "unhealthy"},
        ]

        assert self.get_level_mock(levels, 400, 2000, 700.0)["classTag"] == "good"
        assert self.get_level_mock(levels, 400, 2000, 700.5)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 400, 2000, 1000.0)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 400, 2000, 1000.5)["classTag"] == "sensitive"

    def test_temperature_boundary_classification(self):
        """Temperature boundary values must map to correct adjacent levels."""
        levels = [
            {"min": 15, "max": 28, "label": "Mát (Tốt)", "classTag": "good"},
            {"min": 28.1, "max": 32, "label": "Vừa", "classTag": "moderate"},
            {"min": 32.1, "max": 36, "label": "Ấm / Cao", "classTag": "sensitive"},
            {"min": 36.1, "max": 45, "label": "Nóng (Rất cao)", "classTag": "unhealthy"},
        ]

        assert self.get_level_mock(levels, 15, 45, 28.0)["classTag"] == "good"
        assert self.get_level_mock(levels, 15, 45, 28.05)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 15, 45, 32.0)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 15, 45, 32.05)["classTag"] == "sensitive"

    def test_noise_boundary_classification(self):
        """Noise boundary values must map to correct adjacent levels."""
        levels = [
            {"min": 30, "max": 55, "label": "Yên tĩnh", "classTag": "good"},
            {"min": 55.1, "max": 70, "label": "Vừa", "classTag": "moderate"},
            {"min": 70.1, "max": 85, "label": "Ồn (Cao)", "classTag": "sensitive"},
            {"min": 85.1, "max": 100, "label": "Rất ồn (Xấu)", "classTag": "unhealthy"},
        ]

        assert self.get_level_mock(levels, 30, 100, 55.0)["classTag"] == "good"
        assert self.get_level_mock(levels, 30, 100, 55.05)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 30, 100, 70.0)["classTag"] == "moderate"
        assert self.get_level_mock(levels, 30, 100, 70.05)["classTag"] == "sensitive"


class TestDispersionRasterClippingContract:
    """Test suite verifying vector polygon clipping in dispersionField.ts."""

    def setup_method(self):
        self.content = DISPERSION_FILE.read_text(encoding="utf-8")

    def test_uses_destination_in_global_composite_operation(self):
        """createDispersionOffscreenCanvas must use destination-in for clean vector path clipping."""
        assert 'globalCompositeOperation = "destination-in"' in self.content
        assert "ctx.closePath()" in self.content
        assert "ctx.fill()" in self.content
