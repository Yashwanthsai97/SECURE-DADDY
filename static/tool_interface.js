(function () {
    function initializeTheme() {
        document.body.dataset.theme = "dark";
        document.documentElement.style.colorScheme = "dark";
    }

    window.SecureDaddyTheme = {
        applyTheme: initializeTheme,
        initializeTheme: initializeTheme
    };

    document.addEventListener("DOMContentLoaded", initializeTheme);
})();
