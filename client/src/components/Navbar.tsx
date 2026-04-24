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
        <Link to="/" className="text-xl font-bold tracking-wider text-gray-800">
          אפקה <span className="text-emerald-600">Recommender</span>
        </Link>
        <div className="hidden md:flex gap-4">
          <Link to="/" className="text-gray-500 hover:text-gray-800 transition-colors">לוח בקרה</Link>
          <Link to="/recommendations" className="text-gray-500 hover:text-gray-800 transition-colors">המלצות</Link>
          <Link to="/explorer" className="text-gray-500 hover:text-gray-800 transition-colors">חיפוש קורסים</Link>
          {/* <Link to="/questionnaire" className="text-gray-500 hover:text-gray-800 transition-colors">העדפות</Link> */}
          <Link to="/history" className="text-gray-500 hover:text-gray-800 transition-colors">היסטוריה שלי</Link>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-gray-500 text-sm">שלום, {user.name}</span>
        <button 
          onClick={handleLogout}
          className="bg-gray-100 hover:bg-gray-100 text-gray-800 border border-gray-200 py-1.5 px-4 rounded-lg text-sm transition-all"
        >
          התנתק
        </button>
      </div>
    </nav>
  );
}
