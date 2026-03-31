(function () {
    const themeStorageKey = "securedaddy-theme";

    function getSystemTheme() {
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
            return "light";
        }

        return "dark";
    }

    function readSavedTheme() {
        try {
            const savedTheme = window.localStorage.getItem(themeStorageKey);

            if (savedTheme === "light" || savedTheme === "dark") {
                return savedTheme;
            }
        } catch (error) {
            console.warn("Theme preference could not be read.", error);
        }

        return null;
    }

    function writeSavedTheme(theme) {
        try {
            window.localStorage.setItem(themeStorageKey, theme);
        } catch (error) {
            console.warn("Theme preference could not be saved.", error);
        }
    }

    function applyTheme(theme) {
        const resolvedTheme = theme === "light" ? "light" : "dark";
        const isLightMode = resolvedTheme === "light";
        const themeToggle = document.getElementById("themeToggle");
        const themeToggleText = document.getElementById("themeToggleText");

        document.body.dataset.theme = resolvedTheme;
        document.documentElement.style.colorScheme = resolvedTheme;

        if (!themeToggle) {
            return;
        }

        themeToggle.setAttribute("aria-pressed", String(isLightMode));
        themeToggle.setAttribute("aria-label", isLightMode ? "Switch to dark mode" : "Switch to light mode");

        if (themeToggleText) {
            themeToggleText.textContent = isLightMode ? "Light" : "Dark";
        }
    }

    function initializeTheme() {
        const themeToggle = document.getElementById("themeToggle");

        applyTheme(readSavedTheme() || getSystemTheme());

        if (!themeToggle || themeToggle.dataset.themeReady === "true") {
            return;
        }

        themeToggle.dataset.themeReady = "true";
        themeToggle.addEventListener("click", () => {
            const nextTheme = document.body.dataset.theme === "light" ? "dark" : "light";

            applyTheme(nextTheme);
            writeSavedTheme(nextTheme);
        });

        if (!window.matchMedia) {
            return;
        }

        const colorSchemeQuery = window.matchMedia("(prefers-color-scheme: light)");
        const handleColorSchemeChange = event => {
            if (readSavedTheme()) {
                return;
            }

            applyTheme(event.matches ? "light" : "dark");
        };

        if (typeof colorSchemeQuery.addEventListener === "function") {
            colorSchemeQuery.addEventListener("change", handleColorSchemeChange);
        } else if (typeof colorSchemeQuery.addListener === "function") {
            colorSchemeQuery.addListener(handleColorSchemeChange);
        }
    }

    window.SecureDaddyTheme = {
        applyTheme: applyTheme,
        initializeTheme: initializeTheme
    };

    document.addEventListener("DOMContentLoaded", initializeTheme);
})();
