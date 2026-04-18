import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!user) return null;

  return (
    <nav className="glass-panel sticky top-4 z-50 mx-4 my-4 flex items-center justify-between !py-4">
      <div className="flex items-center gap-6">
        <Link to="/" className="text-xl font-bold tracking-wider text-white">
          Afeka <span className="text-blue-400">Recommender</span>
        </Link>
        <div className="hidden md:flex gap-4">
          <Link to="/" className="text-white/80 hover:text-white transition-colors">Dashboard</Link>
          <Link to="/recommendations" className="text-white/80 hover:text-white transition-colors">Recommendations</Link>
          <Link to="/explorer" className="text-white/80 hover:text-white transition-colors">Courses</Link>
          <Link to="/questionnaire" className="text-white/80 hover:text-white transition-colors">Preferences</Link>
          <Link to="/history" className="text-white/80 hover:text-white transition-colors">My History</Link>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-white/60 text-sm">Hello, {user.name}</span>
        <button 
          onClick={handleLogout}
          className="bg-white/10 hover:bg-white/20 text-white border border-white/20 py-1.5 px-4 rounded-lg text-sm transition-all"
        >
          Sign Out
        </button>
      </div>
    </nav>
  );
}
