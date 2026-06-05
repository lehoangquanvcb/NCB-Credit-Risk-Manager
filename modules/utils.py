import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def load_csv(name):
    return pd.read_csv(DATA_DIR / name)

def status_badge(actual, amber, red, direction="lower"):
    if direction == "higher":
        if actual < red: return "🔴 Red"
        if actual < amber: return "🟡 Amber"
        return "🟢 Green"
    if actual > red: return "🔴 Red"
    if actual > amber: return "🟡 Amber"
    return "🟢 Green"

def format_pct(x):
    return f"{x:.2%}"

def hhi(shares):
    return float((shares ** 2).sum())
