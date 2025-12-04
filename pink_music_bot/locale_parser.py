from pathlib import Path

import yaml


class LocaleParser:
    def __init__(
        self,
        locale_dir: str,
        fallback_locale: str = "en",
        force_fallback: bool = False,
    ):
        self.locale_dir = locale_dir
        self.fallback_locale = fallback_locale
        self.force_fallback = force_fallback
        self.initialize()

    def initialize(self):
        self.translations = {}

        for locale_path in Path(self.locale_dir).glob("*.yaml"):
            locale = locale_path.stem
            self.translations[locale] = yaml.safe_load(
                locale_path.read_text(encoding="utf-8")
            )

        if not self.translations.get(self.fallback_locale):
            raise ValueError(f"Fallback locale '{self.fallback_locale}' not found.")

    def get(self, locale: str, *path: str) -> str:
        translation = self.translations.get(
            locale if not self.force_fallback else self.fallback_locale
        )

        for key in path:
            if isinstance(translation, dict):
                translation = translation.get(key)
            elif isinstance(translation, str):
                break
            else:
                translation = None
                break

        if not isinstance(translation, str):
            translation = self.translations.get(self.fallback_locale)

            for key in path:
                if isinstance(translation, dict):
                    translation = translation.get(key)
                elif isinstance(translation, str):
                    break
                else:
                    translation = None
                    break

        return translation if isinstance(translation, str) else str(path)
