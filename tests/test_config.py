"""Tests para src.utils.config — defaults y estructura."""

from __future__ import annotations

import os

from src.utils.config import (
    LLMConfig,
    OpenSEOConfig,
    PageSpeedConfig,
    WigoloConfig,
    config,
)


class TestConfigStructure:
    """El singleton Config expone todas las secciones esperadas."""

    def test_has_llm(self):
        assert hasattr(config, "llm")

    def test_has_wigolo(self):
        assert hasattr(config, "wigolo")

    def test_has_openseo(self):
        assert hasattr(config, "openseo")

    def test_has_pagespeed(self):
        assert hasattr(config, "pagespeed")

    def test_has_project_root(self):
        assert config.project_root is not None
        assert config.project_root.exists()


class TestLLMConfigDefaults:
    """Valores por defecto cuando no hay variables de entorno."""

    def test_default_model(self):
        original = os.environ.pop("DEEPSEEK_MODEL", None)
        try:
            cfg = LLMConfig()
            assert cfg.model == "deepseek-v4-flash"
        finally:
            if original is not None:
                os.environ["DEEPSEEK_MODEL"] = original

    def test_default_base_url(self):
        cfg = LLMConfig()
        assert cfg.base_url == "https://api.deepseek.com"

    def test_default_temperature(self):
        cfg = LLMConfig()
        assert cfg.temperature == 0.3

    def test_default_max_tokens(self):
        cfg = LLMConfig()
        assert cfg.max_tokens == 4096

    def test_default_api_key_empty(self):
        original = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            cfg = LLMConfig()
            assert cfg.api_key == ""
        finally:
            if original is not None:
                os.environ["DEEPSEEK_API_KEY"] = original


class TestWigoloConfigDefaults:
    def test_default_command(self):
        cfg = WigoloConfig()
        assert cfg.command == "npx"

    def test_default_args(self):
        cfg = WigoloConfig()
        assert cfg.args == ["-y", "wigolo"]


class TestOpenSEOConfigDefaults:
    def test_default_mcp_url(self):
        cfg = OpenSEOConfig()
        assert cfg.mcp_url == "http://localhost:3001/mcp"


class TestPageSpeedConfigDefaults:
    def test_default_base_url(self):
        cfg = PageSpeedConfig()
        assert (
            cfg.base_url
            == "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        )

    def test_default_api_key_empty(self):
        original = os.environ.pop("GOOGLE_PAGESPEED_API_KEY", None)
        try:
            cfg = PageSpeedConfig()
            assert cfg.api_key == ""
        finally:
            if original is not None:
                os.environ["GOOGLE_PAGESPEED_API_KEY"] = original
