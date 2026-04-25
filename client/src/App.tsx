import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { api } from './services/api';
import { useState, useEffect } from 'react';
import Auth from './components/Auth';
import Layout from './components/Layout';
import Recommendations from './pages/Recommendations';
import Questionnaire from './pages/Questionnaire';
import CourseExplorer from './pages/CourseExplorer';
import CourseHistory from './pages/CourseHistory';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';

function App() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      api.getProfile(user.user_id)
        .then(res => setProfile(res.data))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    } else {
      setProfile(null);
      setLoading(false);
    }
  }, [user]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen text-gray-800 text-xl animate-pulse">Loading profile...</div>;
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="pb-10">
          <h1 className="text-3xl font-bold text-gray-700">AI Course Recommender</h1>
        </div>
        <Auth onLogin={() => { }} />
      </div>
    );
  }

  if (profile && !profile.onboarding_completed) {
    return (
      <Routes>
        <Route path="/onboarding" element={<Onboarding onComplete={() => setProfile({...profile, onboarding_completed: true})} />} />
        <Route path="*" element={<Navigate to="/onboarding" replace />} />
      </Routes>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/questionnaire" element={<Questionnaire />} />
        <Route path="/explorer" element={<CourseExplorer />} />
        <Route path="/history" element={<CourseHistory />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;