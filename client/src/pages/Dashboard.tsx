import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [topRecommendation, setTopRecommendation] = useState<any>(null);
  const [schedule, setSchedule] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchData = async () => {
      try {
        const [profileRes, historyRes, recsRes, schedRes] = await Promise.all([
          api.getProfile(user.user_id),
          api.getHistory(user.user_id),
          api.getRecommendations(user.user_id),
          api.getSchedule(user.user_id)
        ]);
        setProfile(profileRes.data);
        setHistory(historyRes.data);
        setSchedule(schedRes.data);
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
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">
          ברוך שובך, {user?.name}
        </h1>
        <p className="text-gray-500 mt-2">הנה סקירה של המצב האקדמי שלך.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Degree Progress Widget */}
        <div className="glass-panel col-span-1 md:col-span-1 flex flex-col items-center justify-center p-6 hover:shadow-teal-500/20 transition-all">
          <h2 className="text-xl font-semibold mb-6 w-full text-right">התקדמות בתואר</h2>
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                className="text-gray-300 stroke-current"
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
            <p className="text-gray-500 text-sm">
              <span className="text-gray-800 font-medium">{earnedCredits}</span> / {totalCredits} נקודות זכות
            </p>
          </div>
        </div>

        {/* Recommendation Hero Section */}
        <div className="glass-panel col-span-1 md:col-span-2 p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -mr-16 -mt-16 transition-transform group-hover:scale-110"></div>
          
          <div className="relative z-10 h-full flex flex-col justify-between">
            <div>
              <div className="inline-block px-3 py-1 bg-yellow-500/20 text-yellow-500 rounded-full text-xs font-semibold mb-4 border border-yellow-500/30">
                #1 המלצה מובילה לסמסטר הבא
              </div>
              {topRecommendation ? (
                <>
                  <h2 className="text-3xl font-bold mb-2">{topRecommendation.course.name}</h2>
                  <p className="text-gray-500 mb-4 line-clamp-2">{topRecommendation.explanation}</p>
                  
                  <div className="flex gap-4 mt-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                      ציון התאמה: {topRecommendation.score}%
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                      עומס: {topRecommendation.course.workload}/5
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-gray-500 italic my-auto">
                  אין המלצות זמינות כרגע.
                </div>
              )}
            </div>

            <div className="mt-8 flex items-center gap-4">
              <Link 
                to="/recommendations"
                className="bg-emerald-600 hover:bg-emerald-500 text-gray-800 px-6 py-2.5 rounded-lg font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)]"
              >
                צפה בכל ההמלצות
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Profile Summary */}
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">ההעדפות שלך</h2>
          <Link to="/questionnaire" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
            עריכת העדפות ←
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">שנת לימודים</div>
            <div className="font-medium text-lg">שנה {profile?.year_of_study || 1}</div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">תואר</div>
            <div className="font-medium text-lg truncate">{profile?.degree || 'מדעי המחשב'}</div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">עומס יעד</div>
            <div className="font-medium text-lg">{profile?.target_workload || 3} / 5</div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">מסלולים</div>
            <div className="font-medium text-sm line-clamp-2">
              {profile?.interested_tracks?.length > 0 
                ? profile.interested_tracks.map((t: any) => t.name).join(', ') 
                : 'לא נבחר'}
            </div>
          </div>
        </div>
      </div>

      {/* My Schedule (System) */}
      <div className="glass-panel p-6 mt-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">מערכת השעות שלי</h2>
          <Link to="/explorer" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
            חיפוש קורסים ←
          </Link>
        </div>
        
        {schedule.length > 0 ? (
          <div className="space-y-3">
            {schedule.map((item, index) => (
              <div key={index} className="flex justify-between items-center p-4 bg-gray-50 border border-gray-200 rounded-xl">
                <div>
                  <h3 className="font-semibold text-gray-800">{item.course.name} <span className="text-sm text-gray-500 font-normal">({item.course_code})</span></h3>
                  <div className="text-sm text-gray-600 mt-1 flex items-center gap-4">
                    <span><strong className="text-emerald-600">יום:</strong> {item.course.day_of_week || 'טרם נקבע'}</span>
                    <span><strong className="text-emerald-600">שעות:</strong> {item.course.start_time || '?'} - {item.course.end_time || '?'}</span>
                    <span><strong className="text-emerald-600">חדר:</strong> {item.course.room || 'טרם נקבע'}</span>
                  </div>
                </div>
                <button 
                  onClick={async () => {
                    if (!user) return;
                    await api.removeSchedule(user.user_id, item.course_code);
                    setSchedule(schedule.filter(s => s.course_code !== item.course_code));
                  }}
                  className="text-red-500 hover:text-red-600 text-sm font-medium pr-4 border-r border-gray-200 mr-4"
                >
                  הסר
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 border border-gray-200 rounded-xl">
            <p className="text-gray-500 mb-4">עדיין לא הוספת קורסים למערכת השעות שלך.</p>
            <Link to="/recommendations" className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-medium transition-all shadow-md shadow-emerald-500/20">
              מצא קורסים
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
