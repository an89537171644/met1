"""Streamlit UI placeholder."""

from __future__ import annotations


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Install UI dependencies with: pip install -e .[ui]") from exc

    st.title("Steel Frame Designer")
    st.info("MVP UI placeholder. Use CLI commands while engineering modules are being built.")
