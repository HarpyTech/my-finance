import { useTheme } from '../theme/ThemeContext';

export default function ThemeToggle({ floating = false }) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      className={floating ? 'theme-toggle theme-toggle-floating' : 'theme-toggle'}
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      <span className="theme-toggle-glyph" aria-hidden="true">
        {isDark ? '☀' : '☾'}
      </span>
      <span>{isDark ? 'Light' : 'Dark'} mode</span>
    </button>
  );
}