import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_LINK_BASE =
  'inline-flex h-10 shrink-0 items-center justify-center px-3 text-sm font-medium leading-none border-b-2 border-transparent box-border transition-colors';

const MOBILE_NAV_LINK_BASE =
  'flex h-11 w-full items-center justify-start px-4 text-sm font-medium leading-none border-b-2 border-transparent box-border transition-colors rounded-lg';

function navLinkClass({ isActive }: { isActive: boolean }) {
  return [
    NAV_LINK_BASE,
    isActive ? 'text-emerald-600 border-emerald-600' : 'text-gray-500 hover:text-gray-800',
  ].join(' ');
}

function mobileNavLinkClass({ isActive }: { isActive: boolean }) {
  return [
    MOBILE_NAV_LINK_BASE,
    isActive
      ? 'bg-emerald-50 text-emerald-600 border-emerald-600'
      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800',
  ].join(' ');
}

const NAV_ITEMS = [
  { to: '/profile', label: 'פרופיל' },
  { to: '/recommendations', label: 'המלצות' },
  { to: '/explorer', label: 'חיפוש קורסים' },
  { to: '/history', label: 'היסטוריה שלי' },
] as const;

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onResize = () => {
      if (window.matchMedia('(min-width: 768px)').matches) {
        setMenuOpen(false);
      }
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    navigate('/');
  };

  if (!user) return null;

  return (
    <nav
      className="glass-panel relative box-border h-16 min-h-16 max-h-16 w-full shrink-0 overflow-visible !p-0"
      aria-label="ניווט ראשי"
    >
      <div className="flex h-full w-full items-center justify-between gap-3 px-1 sm:px-4 box-border">
        <div className="flex min-w-0 flex-1 items-center gap-3 md:gap-6">
          <Link
            to="/"
            className="inline-flex h-10 min-w-0 shrink items-center text-xl font-bold leading-none tracking-wide text-gray-800 box-border sm:text-2xl"
            onClick={() => setMenuOpen(false)}
          >
            <span className="truncate text-emerald-600">AfekAdvisor</span>
          </Link>

          <div className="hidden md:flex min-w-0 items-center gap-1 overflow-x-auto">
            {NAV_ITEMS.map(({ to, label }) => (
              <NavLink key={to} to={to} className={navLinkClass}>
                {label}
              </NavLink>
            ))}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-4">
          <span className="hidden lg:inline max-w-[12rem] truncate text-sm font-medium leading-none text-gray-500">
            שלום, {user.name}
          </span>

          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex h-9 shrink-0 items-center justify-center border border-gray-200 bg-gray-100 px-3 text-sm font-medium leading-none text-gray-800 box-border transition-colors hover:bg-gray-200 sm:px-4"
          >
            התנתק
          </button>

          <button
            type="button"
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-700 box-border transition-colors hover:bg-gray-50 md:hidden"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-controls="mobile-nav-menu"
            aria-label={menuOpen ? 'סגור תפריט' : 'פתח תפריט'}
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden
            >
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {menuOpen && (
        <div
          id="mobile-nav-menu"
          className="absolute inset-x-0 top-[calc(100%+0.5rem)] z-50 md:hidden"
        >
          <div className="glass-panel !p-2 shadow-lg">
            <p className="px-4 py-2 text-xs font-medium text-gray-400 lg:hidden">שלום, {user.name}</p>
            {NAV_ITEMS.map(({ to, label }) => (
              <NavLink key={to} to={to} className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                {label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
