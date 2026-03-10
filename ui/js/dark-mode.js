const darkMode = (() => {
  let currentTheme = null;

  function getSavedTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function updateToggleIcon(theme) {
    const toggle = document.getElementById('darkModeToggle');
    if (!toggle) return;
    const icon = toggle.querySelector('svg');
    if (!icon) return;
    icon.classList.toggle('is-dark', theme === 'dark');
  }

  function updateRouge(theme) {
    const link = document.getElementById('rouge-theme');
    if (!link) return;
    link.href = `${uiRootPath}/css/rouge/${theme === 'dark' ? 'github.dark' : 'github.light'}.css`;
  }

  function applyTheme(theme) {
    if (theme === currentTheme) return;
    currentTheme = theme;

    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    root.style.colorScheme = theme;
    localStorage.setItem('theme', theme);

    if (typeof setRougeTheme === 'function') {
      setRougeTheme(theme === 'dark' ? 'github.dark' : 'github.light');
    }

    // Only update DOM-dependent elements after they exist
    if (document.readyState !== 'loading') {
      updateRouge(theme);
      updateToggleIcon(theme);
    } else {
      document.addEventListener('DOMContentLoaded', () => {
        updateRouge(theme);
        updateToggleIcon(theme);
      });
    }
  }

  return {
    getSavedTheme,
    applyTheme,
  };
})();

// Delegated click handler for toggle button
document.addEventListener('click', (e) => {
  const toggle = e.target.closest('#darkModeToggle');
  if (!toggle) return;
  e.preventDefault();

  const current = darkMode.getSavedTheme();
  darkMode.applyTheme(current === 'dark' ? 'light' : 'dark');
});

// Apply initial theme after DOM is ready 
(function() {
  const theme = darkMode.getSavedTheme();
  darkMode.applyTheme(theme);
})();