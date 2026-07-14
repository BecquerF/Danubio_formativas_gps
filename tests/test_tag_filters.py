import os
import unittest

import pandas as pd

os.environ.setdefault("SECRET_KEY", "test")

from app_filters import build_filter_options, normalize_report_date
import CEGPS_Danubio_Formativas as app_module


class TagFilterOptionsTests(unittest.TestCase):
    def test_normalize_report_date_accepts_iso_and_day_first_inputs(self):
        self.assertEqual(normalize_report_date("2026-05-19"), pd.Timestamp("2026-05-19"))
        self.assertEqual(normalize_report_date("19/05/2026"), pd.Timestamp("2026-05-19"))

    def test_build_filter_options_keeps_only_valid_selected_values(self):
        df = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2026-05-19", "2026-05-21", "2026-05-21"]),
                "Category": ["U18", "U18", "U19"],
                "Activity Tags": ["MD 19", "MD 23", "MD 19"],
            }
        )

        dff = df[df["Category"] == "U18"].copy()
        options, valid_values = build_filter_options(
            dff,
            "Activity Tags",
            current_values=["MD 23", "MD 99"],
        )

        self.assertEqual([item["value"] for item in options], ["MD 19", "MD 23"])
        self.assertEqual(valid_values, ["MD 23"])


class DownloadExportTests(unittest.TestCase):
    def test_build_download_export_frame_supports_activity_tab(self):
        dff = app_module.df.copy()
        fecha = dff["Date"].max()

        export_df = app_module.build_download_export_frame(
            "actividad",
            dff,
            ["Distance"],
            "Category",
            fecha,
        )

        self.assertIsInstance(export_df, pd.DataFrame)
        self.assertFalse(export_df.empty)
        self.assertIn("Distance", export_df.columns)


if __name__ == "__main__":
    unittest.main()
