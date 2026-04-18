import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [topRecommendation, setTopRecommendation] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchData = async () => {
      try {
        const [profileRes, historyRes, recsRes] = await Promise.all([
          api.getProfile(user.user_id),
          api.getHistory(user.user_id),
          api.getRecommendations(user.user_id)
        ]);
        setProfile(profileRes.data);
        setHistory(historyRes.data);
        if (recsRes.data && recsRes.data.length > 0) {
          setTopRecommendation(recsRes.data[0]);
        }
      } catch (err) {
        console.error('Error fetching dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Assuming ~120 credits for degree, each course roughly 3 credits for visual purposes
  const totalCredits = 120;
  const earnedCredits = history.length * 3;
  const progressPercent = Math.min(Math.round((earnedCredits / totalCredits) * 100), 100);

  return (
    <div className="space-y-8 animate-fade-in">
      <header>
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
          Welcome back, {user?.name}
        </h1>
        <p className="text-white/60 mt-2">Here is your academic overview.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Degree Progress Widget */}
        <div className="glass-panel col-span-1 md:col-span-1 flex flex-col items-center justify-center p-6 hover:shadow-purple-500/20 transition-all">
          <h2 className="text-xl font-semibold mb-6 w-full text-left">Degree Progress</h2>
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                className="text-white/10 stroke-current"
                strokeWidth="8"
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
              ></circle>
              <circle
                className="text-purple-500 stroke-current drop-shadow-[0_0_8px_rgba(168,85,247,0.8)] transition-all duration-1000 ease-out"
                strokeWidth="8"
                strokeLinecap="round"
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                strokeDasharray={`${progressPercent * 2.51} 251.2`}
              ></circle>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold">{progressPercent}%</span>
            </div>
          </div>
          <div className="mt-6 text-center">
            <p className="text-white/70 text-sm">
              <span className="text-white font-medium">{earnedCredits}</span> / {totalCredits} Credits Earned
            </p>
          </div>
        </div>

        {/* Recommendation Hero Section */}
        <div className="glass-panel col-span-1 md:col-span-2 p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -mr-16 -mt-16 transition-transform group-hover:scale-110"></div>
          
          <div className="relative z-10 h-full flex flex-col justify-between">
            <div>
              <div className="inline-block px-3 py-1 bg-yellow-500/20 text-yellow-300 rounded-full text-xs font-semibold mb-4 border border-yellow-500/30">
                #1 Recommended Next Semester
              </div>
              {topRecommendation ? (
                <>
                  <h2 className="text-3xl font-bold mb-2">{topRecommendation.course.name}</h2>
                  <p className="text-white/70 mb-4 line-clamp-2">{topRecommendation.explanation}</p>
                  
                  <div className="flex gap-4 mt-4">
                    <div className="flex items-center gap-2 text-sm text-white/60">
                      <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                      Score: {topRecommendation.score}%
                    </div>
                    <div className="flex items-center gap-2 text-sm text-white/60">
                      <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                      Workload: {topRecommendation.course.workload}/5
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-white/60 italic my-auto">
                  No recommendations available at this time.
                </div>
              )}
            </div>

            <div className="mt-8 flex items-center gap-4">
              <Link 
                to="/recommendations"
                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)]"
              >
                View All Recommendations
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Profile Summary */}
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Your Profile Profile</h2>
          <Link to="/questionnaire" className="text-sm text-blue-400 hover:text-blue-300">
            Edit Preferences →
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="text-white/50 text-xs mb-1 uppercase tracking-wider">Year of Study</div>
            <div className="font-medium text-lg">Year {profile?.year_of_study || 1}</div>
          </div>
          <div className="bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="text-white/50 text-xs mb-1 uppercase tracking-wider">Degree</div>
            <div className="font-medium text-lg truncate">{profile?.degree || 'Computer Science'}</div>
          </div>
          <div className="bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="text-white/50 text-xs mb-1 uppercase tracking-wider">Target Workload</div>
            <div className="font-medium text-lg">{profile?.target_workload || 3} / 5</div>
          </div>
          <div className="bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="text-white/50 text-xs mb-1 uppercase tracking-wider">Tracks</div>
            <div className="font-medium text-sm line-clamp-2">
              {profile?.interested_tracks?.length > 0 
                ? profile.interested_tracks.map((t: any) => t.name).join(', ') 
                : 'None Selected'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
