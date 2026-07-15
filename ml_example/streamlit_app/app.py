import csv
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from ml_example.ml_training.pipeline.predict import MODEL_VERSION, predict_fault_from_inputs

DEFAULT_API_BASE_URL = "http://localhost:8000"
TAB1_MODEL_VERSION = "2.0"
PREDICTION_LOG_PATH = Path("ml_example/reports/prediction_logs.csv")
TRAINING_PREDICTIONS_PATH = Path("ml_example/reports/training_predictions.csv")
VISUALIZATION_DIR = Path("ml_example/visualization")

# -----------------------------------------------------------------------------
# Non-Streamlit helpers
# -----------------------------------------------------------------------------
def load_prediction_logs(path: Path) -> pd.DataFrame:
    columns = ["timestamp", "source", "prediction", "confidence", "true_label", "latency_ms"]
    if not path.exists():
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(path)
    except pd.errors.ParserError:
        with path.open("r", encoding="utf-8", newline="") as src:
            reader = csv.reader(src)
            all_rows = list(reader)

        if not all_rows:
            return pd.DataFrame(columns=columns)

        header = all_rows[0]
        has_header = "timestamp" in header and "prediction" in header
        data_rows = all_rows[1:] if has_header else all_rows
        index_by_name = {name: idx for idx, name in enumerate(header)} if has_header else {}

        normalized_rows: list[dict[str, object]] = []
        for raw in data_rows:
            if not raw:
                continue
            normalized = {col: "" for col in columns}
            if has_header:
                for col in columns:
                    idx = index_by_name.get(col)
                    if idx is not None and idx < len(raw):
                        normalized[col] = raw[idx]
            else:
                if len(raw) > 0:
                    normalized["timestamp"] = raw[0]
                if len(raw) > 1:
                    normalized["source"] = raw[1]
                if len(raw) > 2:
                    normalized["prediction"] = raw[2]
                if len(raw) > 3:
                    normalized["confidence"] = raw[3]
                if len(raw) > 4:
                    normalized["latency_ms"] = raw[4]
            normalized_rows.append(normalized)

        df = pd.DataFrame(normalized_rows, columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def load_train_data_from_api(api_base_url: str) -> pd.DataFrame:
    response = requests.get(f"{api_base_url}/train-data", params={"limit": 50000}, timeout=20)
    response.raise_for_status()

    body = response.json()
    rows = body.get("rows", [])
    if not rows:
        raise ValueError("FastAPI /train-data returned no rows")

    return pd.DataFrame(rows)


def get_serving_model_state(api_base_url: str) -> dict[str, object]:
    response = requests.get(f"{api_base_url}/serving-model", timeout=10)
    response.raise_for_status()
    return response.json()


def update_serving_model(api_base_url: str, version: str) -> dict[str, object]:
    response = requests.post(
        f"{api_base_url}/serving-model",
        json={"version": version},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def default_input_values(df: pd.DataFrame) -> dict[str, float]:
    row = df.iloc[0]
    return {
        "X_Minimum": float(row["X_Minimum"]),
        "X_Maximum": float(row["X_Maximum"]),
        "Y_Minimum": float(row["Y_Minimum"]),
        "Y_Maximum": float(row["Y_Maximum"]),
        "Pixels_Areas": float(row["Pixels_Areas"]),
        "X_Perimeter": float(row["X_Perimeter"]),
        "Y_Perimeter": float(row["Y_Perimeter"]),
        "Minimum_of_Luminosity": float(row["Minimum_of_Luminosity"]),
        "Maximum_of_Luminosity": float(row["Maximum_of_Luminosity"]),
        "Steel_Plate_Thickness": float(row["Steel_Plate_Thickness"]),
    }


def load_training_predictions(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "timestamp",
                "source",
                "prediction",
                "confidence",
                "target_label",
                "true_label",
                "latency_ms",
            ]
        )
    return pd.read_csv(path)


def combine_prediction_history(
    prediction_logs: pd.DataFrame, training_predictions: pd.DataFrame
) -> pd.DataFrame:
    if "true_label" not in prediction_logs.columns:
        prediction_logs["true_label"] = ""
    if "latency_ms" not in prediction_logs.columns:
        prediction_logs["latency_ms"] = ""

    if "target_label" in training_predictions.columns:
        training_predictions["true_label"] = training_predictions["target_label"].astype(str)
    elif "true_label" not in training_predictions.columns:
        training_predictions["true_label"] = ""
    if "latency_ms" not in training_predictions.columns:
        training_predictions["latency_ms"] = ""

    combined = pd.concat(
        [
            prediction_logs[
                ["timestamp", "source", "prediction", "confidence", "true_label", "latency_ms"]
            ],
            training_predictions[
                ["timestamp", "source", "prediction", "confidence", "true_label", "latency_ms"]
            ],
        ],
        ignore_index=True,
    )
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], errors="coerce")
    combined["confidence"] = pd.to_numeric(combined["confidence"], errors="coerce")
    combined["latency_ms"] = pd.to_numeric(combined["latency_ms"], errors="coerce")
    return combined.dropna(subset=["timestamp"])


# -----------------------------------------------------------------------------
# Streamlit rendering helpers
# -----------------------------------------------------------------------------
def render_model_inputs(key_prefix: str, defaults: dict[str, float]) -> dict[str, float]:
    st.markdown("### Input Features")
    col1, col2 = st.columns(2)

    x_minimum = col1.number_input(
        "X_Minimum", value=defaults["X_Minimum"], step=1.0, key=f"x_min_{key_prefix}"
    )
    x_maximum = col2.number_input(
        "X_Maximum", value=defaults["X_Maximum"], step=1.0, key=f"x_max_{key_prefix}"
    )
    y_minimum = col1.number_input(
        "Y_Minimum", value=defaults["Y_Minimum"], step=1.0, key=f"y_min_{key_prefix}"
    )
    y_maximum = col2.number_input(
        "Y_Maximum", value=defaults["Y_Maximum"], step=1.0, key=f"y_max_{key_prefix}"
    )
    pixels_areas = col1.number_input(
        "Pixels_Areas",
        min_value=1.0,
        value=defaults["Pixels_Areas"],
        step=1.0,
        key=f"pixels_{key_prefix}",
    )
    x_perimeter = col2.number_input(
        "X_Perimeter",
        min_value=1.0,
        value=defaults["X_Perimeter"],
        step=1.0,
        key=f"xp_{key_prefix}",
    )
    y_perimeter = col1.number_input(
        "Y_Perimeter",
        min_value=1.0,
        value=defaults["Y_Perimeter"],
        step=1.0,
        key=f"yp_{key_prefix}",
    )
    min_lumi = col2.number_input(
        "Minimum_of_Luminosity",
        min_value=0.0,
        value=defaults["Minimum_of_Luminosity"],
        step=1.0,
        key=f"min_l_{key_prefix}",
    )
    max_lumi = col1.number_input(
        "Maximum_of_Luminosity",
        min_value=0.0,
        value=defaults["Maximum_of_Luminosity"],
        step=1.0,
        key=f"max_l_{key_prefix}",
    )
    steel_thickness = col2.number_input(
        "Steel_Plate_Thickness",
        min_value=1.0,
        value=defaults["Steel_Plate_Thickness"],
        step=1.0,
        key=f"thickness_{key_prefix}",
    )

    return {
        "X_Minimum": x_minimum,
        "X_Maximum": x_maximum,
        "Y_Minimum": y_minimum,
        "Y_Maximum": y_maximum,
        "Pixels_Areas": pixels_areas,
        "X_Perimeter": x_perimeter,
        "Y_Perimeter": y_perimeter,
        "Minimum_of_Luminosity": min_lumi,
        "Maximum_of_Luminosity": max_lumi,
        "Steel_Plate_Thickness": steel_thickness,
    }


def render_tab1(defaults: dict[str, float]) -> None:
    st.subheader("Direct ML Prediction (Streamlit Only)")
    st.info(f"Model version for Tab 1: {TAB1_MODEL_VERSION}")
    payload = render_model_inputs("t1", defaults)

    if st.button("Predict", key="tab1_predict"):
        result = predict_fault_from_inputs(
            **payload,
            source="UI",
            model_version=TAB1_MODEL_VERSION,
        )
        prediction = str(result["prediction"])
        confidence = float(result["confidence"])
        class_probs = result.get("class_probabilities", {})

        st.markdown("### Prediction")
        st.success(prediction)
        st.write(f"Confidence: {confidence * 100:.1f}%")

        st.markdown("### Feature Summary")
        summary_df = pd.DataFrame({"Input": list(payload.keys()), "Value": list(payload.values())})
        st.dataframe(summary_df, hide_index=True, use_container_width=True)

        if class_probs:
            st.markdown("### Class Probabilities")
            probs_df = pd.DataFrame(
                {"Class": list(class_probs.keys()), "Probability": list(class_probs.values())}
            )
            st.dataframe(probs_df, hide_index=True, use_container_width=True)
            st.bar_chart(probs_df.set_index("Class")["Probability"])


def render_tab2(defaults: dict[str, float], api_base_url: str) -> None:
    st.subheader("API ML Prediction (Streamlit + FastAPI)")
    st.caption("Streamlit calls FastAPI /predict over HTTP")

    serving_state: dict[str, object] | None = None
    try:
        serving_state = get_serving_model_state(api_base_url)
    except requests.RequestException as exc:
        st.warning(f"Could not read current FastAPI serving model: {exc}")

    if serving_state:
        versions = [str(item) for item in serving_state.get("supported_versions", [])]
        active_version = str(serving_state.get("active_version", MODEL_VERSION))
        st.write(f"Current FastAPI served model version: {active_version}")
        if versions:
            st.caption(f"Supported versions: {', '.join(versions)}")

    payload = render_model_inputs("t2", defaults)
    if st.button("Call Prediction API", key="tab2_predict"):
        start = perf_counter()
        try:
            response = requests.post(f"{api_base_url}/predict", json=payload, timeout=10)
            latency_ms = (perf_counter() - start) * 1000
            st.markdown("### API Response")
            st.write("Status:", f"{response.status_code} {response.reason}")
            st.write("Latency:", f"{latency_ms:.1f} ms")

            if response.ok:
                body = response.json()
                st.json(body)
                st.write("Model Version:", body.get("model_version", "unknown"))
                if body.get("class_probabilities"):
                    probs_df = pd.DataFrame(
                        {
                            "Class": list(body["class_probabilities"].keys()),
                            "Probability": list(body["class_probabilities"].values()),
                        }
                    )
                    st.dataframe(probs_df, hide_index=True, use_container_width=True)
                    st.bar_chart(probs_df.set_index("Class")["Probability"])
            else:
                st.error(response.text)
        except requests.RequestException as exc:
            st.error(f"API call failed: {exc}")


def render_tab3(train_df: pd.DataFrame) -> None:
    st.subheader("Signal Visualization Dashboard")
    VISUALIZATION_DIR.mkdir(parents=True, exist_ok=True)

    df = train_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()
    df["machine_id"] = np.where(df["TypeOfSteel_A300"] == 1, "M_A300", "M_A400")
    df["Luminosity_Range"] = df["Maximum_of_Luminosity"] - df["Minimum_of_Luminosity"]

    st.markdown("### Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    machine = filter_col1.selectbox("Machine", sorted(df["machine_id"].unique()), index=0)
    signal = filter_col2.selectbox(
        "Signal", ["Pixels_Areas", "X_Perimeter", "Y_Perimeter", "Luminosity_Range"], index=0
    )
    date_min = df["timestamp"].min().date()
    date_max = df["timestamp"].max().date()
    date_range = filter_col3.date_input(
        "Date Range", value=(date_min, date_max), min_value=date_min, max_value=date_max
    )
    filter_col4, filter_col5 = st.columns(2)
    aggregation = filter_col4.selectbox(
        "Aggregation", ["1 minute", "5 minute", "15 minute"], index=1
    )
    selected_signals = filter_col5.multiselect(
        "Multiple Signals",
        ["Pixels_Areas", "X_Perimeter", "Y_Perimeter", "Luminosity_Range"],
        default=["Pixels_Areas", "Luminosity_Range"],
    )

    machine_df = df[df["machine_id"] == machine].copy()

    if isinstance(date_range, tuple | list) and len(date_range) == 2:
        start_date, end_date = date_range
        machine_df = machine_df[
            (machine_df["timestamp"].dt.date >= start_date)
            & (machine_df["timestamp"].dt.date <= end_date)
        ]

    freq_map = {"1 minute": "1min", "5 minute": "5min", "15 minute": "15min"}
    resampled = (
        machine_df.set_index("timestamp")
        [["Pixels_Areas", "X_Perimeter", "Y_Perimeter", "Luminosity_Range"]]
        .resample(freq_map[aggregation])
        .mean()
        .reset_index()
    )
    resampled = resampled.dropna(subset=[signal])

    if machine_df.empty or resampled.empty:
        st.warning(
            "No rows match the selected filters. Expand the date range or choose another machine."
        )
        st.stop()

    st.markdown("### Signal Trend")
    trend_fig = px.line(
        resampled,
        x="timestamp",
        y=signal,
        title=f"{signal} over Time ({machine}) from data/raw/train.csv",
    )
    st.plotly_chart(trend_fig, use_container_width=True)

    if selected_signals:
        st.markdown("### Multiple Signals")
        multi_fig = px.line(
            resampled,
            x="timestamp",
            y=selected_signals,
            title=f"Signals ({machine}) from raw train data",
        )
        st.plotly_chart(multi_fig, use_container_width=True)

    st.markdown("### Correlation")
    if len(selected_signals) != 2:
        st.info("Select exactly 2 signals in 'Multiple Signals' to compute pairwise correlation.")
    else:
        signal_x, signal_y = selected_signals
        corr_data = resampled[[signal_x, signal_y]].dropna()
        if corr_data.empty:
            st.warning(
                "No overlapping values available to compute correlation for selected signals."
            )
        else:
            corr_value = corr_data[signal_x].corr(corr_data[signal_y])
            st.write(f"Pearson correlation ({signal_x} vs {signal_y}): {corr_value:.4f}")
            corr_fig = px.scatter(
                corr_data,
                x=signal_x,
                y=signal_y,
                title=f"{signal_x} vs {signal_y}",
                opacity=0.5,
            )
            st.plotly_chart(corr_fig, use_container_width=True)


def render_tab4() -> None:
    st.subheader("ML Operations Dashboard")

    st.markdown("### Model Information")
    model_info = {
        "Name": "Steel Fault Predictor",
        "Algorithm": "LightGBM",
        "Version": f"Default={MODEL_VERSION} (Tab 1 hard-coded={TAB1_MODEL_VERSION})",
        "Training Date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "Training Samples": "from train_processed.csv",
        "Features": "6 engineered",
    }
    st.table(pd.DataFrame(model_info.items(), columns=["Field", "Value"]))

    prediction_logs = load_prediction_logs(PREDICTION_LOG_PATH)
    training_predictions = load_training_predictions(TRAINING_PREDICTIONS_PATH)
    combined = combine_prediction_history(prediction_logs, training_predictions)

    st.markdown("### Prediction Metrics")
    prediction_total = int(len(combined))
    non_other_faults = (
        int((combined["prediction"] != "Other_Faults").sum()) if prediction_total else 0
    )
    avg_confidence = float(combined["confidence"].mean()) if prediction_total else 0.0
    latency_only = combined[combined["source"].isin(["UI", "API"])]["latency_ms"].dropna()
    avg_latency_ms = float(latency_only.mean()) if not latency_only.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Predictions", f"{prediction_total:,}")
    col2.metric("Fault Predictions", f"{non_other_faults:,}")
    col3.metric("Average Confidence", f"{avg_confidence * 100:.1f}%")
    col4.metric("Average Latency", f"{avg_latency_ms:.2f} ms" if avg_latency_ms else "N/A")

    st.markdown("### Latency Over Time (UI/API)")
    latency_df = (
        combined[combined["source"].isin(["UI", "API"])].dropna(subset=["latency_ms"]).copy()
    )
    if latency_df.empty:
        st.info("No latency data yet. Run predictions from Tab 1 or Tab 2.")
    else:
        latency_fig = px.line(
            latency_df.sort_values("timestamp"),
            x="timestamp",
            y="latency_ms",
            color="source",
            title="Prediction Latency",
        )
        st.plotly_chart(latency_fig, use_container_width=True)

    st.markdown("### Prediction History")
    full_history = combined.sort_values("timestamp", ascending=False)
    history = full_history.head(500)
    full_history_with_labels = full_history[full_history["true_label"].astype(str).str.len() > 0]

    filter_cols = st.columns(4)
    if not full_history_with_labels.empty:
        default_date = full_history_with_labels["timestamp"].max().date()
    elif not history.empty:
        default_date = history["timestamp"].max().date()
    else:
        default_date = datetime.now(UTC).date()
    date_filter = filter_cols[0].date_input("Date", value=default_date)
    source_filter = filter_cols[1].selectbox(
        "Source", ["All"] + sorted(history["source"].astype(str).unique())
    )
    prediction_filter = filter_cols[2].selectbox(
        "Prediction Type", ["All"] + sorted(history["prediction"].astype(str).unique())
    )
    min_conf = filter_cols[3].slider(
        "Confidence Range", min_value=0.0, max_value=1.0, value=0.0, step=0.01
    )

    filtered = history[history["timestamp"].dt.date == date_filter]
    if source_filter != "All":
        filtered = filtered[filtered["source"] == source_filter]
    if prediction_filter != "All":
        filtered = filtered[filtered["prediction"] == prediction_filter]
    filtered = filtered[filtered["confidence"] >= min_conf]

    st.dataframe(
        filtered[["timestamp", "source", "prediction", "true_label", "confidence", "latency_ms"]],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### Confusion Matrix (Known Labels)")
    known = filtered[filtered["true_label"].astype(str).str.len() > 0]
    if known.empty:
        # Keep source/prediction/confidence filters, but ignore date
        # when no labels exist on selected date.
        fallback_known = full_history[full_history["true_label"].astype(str).str.len() > 0]
        if source_filter != "All":
            fallback_known = fallback_known[fallback_known["source"] == source_filter]
        if prediction_filter != "All":
            fallback_known = fallback_known[fallback_known["prediction"] == prediction_filter]
        fallback_known = fallback_known[fallback_known["confidence"] >= min_conf]

        if fallback_known.empty:
            st.info("No rows with known true labels for current filters.")
        else:
            st.warning(
                "No labeled rows for selected date. "
                "Showing confusion matrix from latest labeled rows "
                "that match other filters."
            )
            conf = pd.crosstab(
                fallback_known["true_label"], fallback_known["prediction"], dropna=False
            )
            st.dataframe(conf, use_container_width=True)
    else:
        conf = pd.crosstab(known["true_label"], known["prediction"], dropna=False)
        st.dataframe(conf, use_container_width=True)


def render_app() -> None:
    st.set_page_config(page_title="ML Architecture Demo", layout="wide")
    st.title("ML Deployment Architecture Demo")
    st.caption("Using raw steel fault train dataset with feature engineering")

    st.sidebar.header("Pages")
    page = st.sidebar.radio(
        "Select a page",
        [
            "Tab 1 - Direct ML Prediction",
            "Tab 2 - API ML Prediction",
            "Tab 3 - Signal Visualization",
            "Tab 4 - ML Operations Dashboard",
        ],
    )

    st.sidebar.header("API Settings")
    api_base_url = st.sidebar.text_input("FastAPI Base URL", value=DEFAULT_API_BASE_URL)

    try:
        train_df = load_train_data_from_api(api_base_url)
    except (requests.RequestException, ValueError) as exc:
        st.error(f"Unable to load train data from FastAPI: {exc}")
        st.stop()

    defaults = default_input_values(train_df)

    if page == "Tab 1 - Direct ML Prediction":
        render_tab1(defaults)
    elif page == "Tab 2 - API ML Prediction":
        render_tab2(defaults, api_base_url)
    elif page == "Tab 3 - Signal Visualization":
        render_tab3(train_df)
    elif page == "Tab 4 - ML Operations Dashboard":
        render_tab4()


if __name__ == "__main__":
    render_app()
