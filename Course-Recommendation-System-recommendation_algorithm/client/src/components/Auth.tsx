import React, { useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Auth({ onLogin }: { onLogin?: () => void }) {
  const { login } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await api.login({ email, password });
        login(res.data);
      } else {
        await api.register({ email, password, name });
        const res = await api.login({ email, password });
        login(res.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel w-[400px] max-w-[90vw] !p-8 animate-fade-in">
      <h2 className="text-center mb-8 text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">
        {isLogin ? 'ברוך שובך' : 'הצטרף לפלטפורמה'}
      </h2>
      
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-center py-2 px-4 rounded-lg mb-6 text-sm">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {!isLogin && (
          <input 
            type="text" 
            placeholder="שם מלא" 
            value={name} 
            onChange={(e) => setName(e.target.value)} 
            required 
            className="w-full bg-gray-100 border border-gray-200 rounded-lg p-3 text-gray-800 focus:outline-none focus:border-emerald-400 transition-colors"
          />
        )}
        <input 
          type="email" 
          placeholder="כתובת אימייל" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
          className="w-full bg-gray-100 border border-gray-200 rounded-lg p-3 text-gray-800 focus:outline-none focus:border-emerald-400 transition-colors"
        />
        <input 
          type="password" 
          placeholder="סיסמה" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
          className="w-full bg-gray-100 border border-gray-200 rounded-lg p-3 text-gray-800 focus:outline-none focus:border-emerald-400 transition-colors"
        />
        <button 
          type="submit" 
          disabled={loading} 
          className="mt-4 bg-emerald-600 hover:bg-emerald-500 py-3 rounded-lg font-medium shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50"
        >
          {loading ? 'מעבד...' : (isLogin ? 'התחבר' : 'צור חשבון')}
        </button>
      </form>
      
      <div className="text-center mt-8 text-sm text-gray-500">
        {isLogin ? "אין לך חשבון? " : "יש לך כבר חשבון? "}
        <button 
          type="button"
          onClick={() => setIsLogin(!isLogin)} 
          className="text-teal-600 hover:text-teal-700 font-medium transition-colors mr-1 bg-transparent border-none p-0 shadow-none hover:shadow-none hover:-translate-y-0"
        >
          {isLogin ? 'הרשם' : 'התחבר'}
        </button>
      </div>
    </div>
  );
}
