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
    <div className="w-full sticky top-0 z-50 bg-white shadow-md" dir="rtl">
      <nav className="mx-auto max-w-6xl flex items-center justify-between py-4 px-8">
        
        <div className="flex items-center gap-10">
          <Link to="/" className="text-2xl font-black text-gray-800 hover:opacity-80 transition-all">
            אפקה <span className="text-emerald-600">Recommender</span>
          </Link>
          
          <div className="hidden lg:flex gap-8">
            <Link to="/" className="text-gray-500 hover:text-emerald-600 font-bold text-sm transition-colors">לוח בקרה</Link>
            <Link to="/profile" className="text-gray-500 hover:text-emerald-600 font-bold text-sm transition-colors">פרופיל</Link>
            <Link to="/recommendations" className="text-gray-500 hover:text-emerald-600 font-bold text-sm transition-colors">המלצות</Link>
            <Link to="/explorer" className="text-gray-500 hover:text-emerald-600 font-bold text-sm transition-colors">חיפוש קורסים</Link>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="hidden sm:flex flex-col items-start leading-tight border-r pr-5 border-gray-200">
            <span className="text-gray-400 text-[10px] uppercase font-black">סטודנט/ית</span>
            <span className="text-gray-900 text-sm font-black">{user.name}</span>
          </div>
          
          <button 
            onClick={handleLogout}
            className="bg-gray-50 hover:bg-red-50 hover:text-red-600 text-gray-500 border border-gray-100 py-2 px-5 rounded-xl text-xs font-black transition-all"
          >
            התנתק
          </button>
        </div>
      </nav>
    </div>
  );
}