import io
import time
import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.linear_model import BayesianRidge
from sklearn.ensemble import RandomForestRegressor
from app.config import settings

class TabPFNEngine:
    """
    TabPFN-3.5 Tabular Foundation Model & Prior Labs Pricing Predictor.
    Predicts optimal marketplace pricing, demand elasticity curves, and inventory anomalies from CSVs.
    """

    def __init__(self):
        self.api_key = settings.tabpfn_api_key
        self.hf_token = settings.hf_token

    def _load_dataframe(self, csv_data: str) -> pd.DataFrame:
        if isinstance(csv_data, str) and csv_data.endswith(".csv") and os.path.exists(csv_data):
            return pd.read_csv(csv_data)
        elif isinstance(csv_data, str):
            return pd.read_csv(io.StringIO(csv_data))
        elif isinstance(csv_data, pd.DataFrame):
            return csv_data
        raise ValueError("Invalid CSV data format")

    def analyze_and_predict(
        self,
        csv_source: Any,
        candidate_item: Dict[str, Any],
        target_col: str = "final_price"
    ) -> Dict[str, Any]:
        start_time = time.time()
        df = self._load_dataframe(csv_source)

        if target_col not in df.columns:
            # Auto-detect target column if default isn't found
            candidates = [c for c in ["final_price", "price", "sale_price", "units_sold"] if c in df.columns]
            if candidates:
                target_col = candidates[0]
            else:
                target_col = df.columns[-1]

        # Identify numeric feature columns excluding item_id, product_name, and target
        ignore_cols = {"item_id", "id", "product_name", "title", "name", target_col}
        feature_cols = [c for c in df.columns if c not in ignore_cols and pd.api.types.is_numeric_dtype(df[c])]

        if not feature_cols:
            raise ValueError("No numeric feature columns found in dataset")

        X_train = df[feature_cols].fillna(df[feature_cols].median()).values
        y_train = df[target_col].fillna(df[target_col].median()).values

        # Build candidate vector
        candidate_vector = []
        for col in feature_cols:
            if col in candidate_item:
                candidate_vector.append(float(candidate_item[col]))
            else:
                candidate_vector.append(float(df[col].median()))
        X_test = np.array([candidate_vector])

        # Attempt TabPFN Regressor first
        tabpfn_success = False
        model_name = "TabPFN-3.5 Foundation Model"
        model_note = ""

        try:
            from tabpfn import TabPFNRegressor
            reg = TabPFNRegressor(device="cpu")
            reg.fit(X_train, y_train)
            predicted_price = float(reg.predict(X_test)[0])
            tabpfn_success = True
            model_note = "Inference executed via TabPFN tabular foundation model."
        except Exception as e:
            # Fallback to Bayesian Ridge Prior
            model_name = "Bayesian Prior Estimator (TabPFN Fallback Baseline)"
            model_note = f"Prior Labs gated token notice: {str(e)[:120]}... Set TABPFN_API_KEY or HF_TOKEN to unlock direct TabPFN-3.5 weights."
            bayes = BayesianRidge()
            bayes.fit(X_train, y_train)
            predicted_price = float(bayes.predict(X_test)[0])

        # Ensure realistic price boundary
        predicted_price = max(round(predicted_price, 2), 1.0)

        # Estimate demand (units sold)
        competitor_price = float(candidate_item.get("competitor_avg_price", predicted_price))
        material_cost = float(candidate_item.get("material_cost", candidate_item.get("creation_hours", 5.0) * 2.0))
        labor_hours = float(candidate_item.get("labor_hours", 0.5))
        base_labor_rate = 25.0  # $25/hr fair artisan wage

        # Calculate Price Elasticity Curve: test variations from -30% to +30%
        elasticity_points = []
        test_multipliers = [0.70, 0.80, 0.90, 1.0, 1.10, 1.20, 1.30]
        base_demand = float(df["units_sold"].median()) if "units_sold" in df.columns else 120.0

        for mult in test_multipliers:
            test_price = round(predicted_price * mult, 2)
            # Elasticity formula: demand decreases as price exceeds competitor benchmarks
            price_ratio = test_price / max(competitor_price, 1.0)
            adjusted_demand = max(int(base_demand * (1.8 - (0.9 * price_ratio))), 5)
            gross_revenue = round(test_price * adjusted_demand, 2)
            unit_cost = material_cost + (labor_hours * base_labor_rate)
            profit = round((test_price - unit_cost) * adjusted_demand, 2)

            elasticity_points.append({
                "price": test_price,
                "multiplier": f"{int((mult - 1.0) * 100):+d}%",
                "predicted_units": adjusted_demand,
                "projected_revenue": gross_revenue,
                "projected_profit": profit,
                "is_recommended": (mult == 1.0)
            })

        # Anomaly detection in historical data:
        # Flag historical items with low margins or large deviation from fair value
        anomalies = []
        unit_costs = []
        for idx, row in df.iterrows():
            m_cost = float(row.get("material_cost", 0))
            l_hrs = float(row.get("labor_hours", 0.5))
            f_price = float(row.get(target_col, 0))
            c_cost = m_cost + (l_hrs * base_labor_rate)
            unit_costs.append(c_cost)
            margin = ((f_price - c_cost) / max(f_price, 1.0)) * 100
            if margin < 15.0 or f_price < c_cost:
                anomalies.append({
                    "item_name": str(row.get("product_name", f"Item #{idx+1}")),
                    "current_price": f"${f_price:.2f}",
                    "estimated_cost": f"${c_cost:.2f}",
                    "margin_percent": f"{margin:.1f}%",
                    "status": "Severely Underpriced (Negative/Low Margin)" if margin < 5 else "Sub-optimal Margin"
                })

        unit_cost = material_cost + (labor_hours * base_labor_rate)
        recommended_demand = [p["predicted_units"] for p in elasticity_points if p["is_recommended"]][0]
        projected_monthly_revenue = round(predicted_price * recommended_demand, 2)
        projected_monthly_profit = round((predicted_price - unit_cost) * recommended_demand, 2)
        margin_percent = round(((predicted_price - unit_cost) / max(predicted_price, 1.0)) * 100, 1)

        return {
            "target_column": target_col,
            "feature_columns": feature_cols,
            "training_samples_count": len(df),
            "optimal_recommended_price": predicted_price,
            "unit_production_cost": round(unit_cost, 2),
            "estimated_units_sold": recommended_demand,
            "projected_monthly_revenue": projected_monthly_revenue,
            "projected_monthly_profit": projected_monthly_profit,
            "profit_margin_percent": margin_percent,
            "elasticity_curve": elasticity_points,
            "historical_anomalies_found": len(anomalies),
            "historical_anomalies": anomalies[:5],  # top 5
            "_meta": {
                "model_engine": model_name,
                "tabpfn_activated": tabpfn_success,
                "note": model_note,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "dataset_size": f"{len(df)} rows, {len(feature_cols)} features"
            }
        }

tabpfn_engine = TabPFNEngine()
