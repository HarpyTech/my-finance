import { NavLink } from 'react-router-dom';

const MENU_ITEMS = [
  { to: '/dashboard', icon: 'DB', label: 'Dashboard' },
  { to: '/report', icon: 'RP', label: 'Report' },
  { to: '/add-expense', icon: '+', label: 'Add Expense' },
];

export default function TopNavigation() {
  return (
    <nav className="top-menu" aria-label="Primary navigation">
      {MENU_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            isActive ? 'top-menu-link active' : 'top-menu-link'
          }
        >
          <span className="top-menu-icon" aria-hidden="true">
            {item.icon}
          </span>
          <span className="top-menu-label">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
