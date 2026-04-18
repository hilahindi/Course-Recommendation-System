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
      <h2 className="text-center mb-8 text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
        {isLogin ? 'Welcome Back' : 'Join the Platform'}
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
            placeholder="Full Name" 
            value={name} 
            onChange={(e) => setName(e.target.value)} 
            required 
            className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-blue-400 transition-colors"
          />
        )}
        <input 
          type="email" 
          placeholder="Email Address" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
          className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-blue-400 transition-colors"
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
          className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-blue-400 transition-colors"
        />
        <button 
          type="submit" 
          disabled={loading} 
          className="mt-4 bg-blue-600 hover:bg-blue-500 py-3 rounded-lg font-medium shadow-lg shadow-blue-500/30 transition-all disabled:opacity-50"
        >
          {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
        </button>
      </form>
      
      <div className="text-center mt-8 text-sm text-white/60">
        {isLogin ? "Don't have an account? " : "Already have an account? "}
        <button 
          type="button"
          onClick={() => setIsLogin(!isLogin)} 
          className="text-purple-400 hover:text-purple-300 font-medium transition-colors ml-1 bg-transparent border-none p-0 shadow-none hover:shadow-none hover:-translate-y-0"
        >
          {isLogin ? 'Sign Up' : 'Log In'}
        </button>
      </div>
    </div>
  );
}
