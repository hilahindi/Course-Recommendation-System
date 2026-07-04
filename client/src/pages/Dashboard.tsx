import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, getCacheEntry } from '../services/api';
import { Link } from 'react-router-dom';
import CourseDetailModal from '../components/CourseDetailModal';
import ReviewModal from '../components/ReviewModal';

function dashboardHasWarmCache(userId: number) {
  return Boolean(
    getCacheEntry(`profile:${userId}`) &&
    getCacheEntry('recommendations') &&
    getCacheEntry(`schedule:${userId}`) &&
    getCacheEntry('roadmap'),
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const userId = user?.user_id;
  const [profile, setProfile] = useState<any>(() =>
    userId ? getCacheEntry(`profile:${userId}`) : null,
  );
  const [roadmapSummary, setRoadmapSummary] = useState<any>(
    () => getCacheEntry<any>('roadmap')?.summary ?? null,
  );
  const [topRecommendation, setTopRecommendation] = useState<any>(() => {
    const recs = getCacheEntry<any[]>('recommendations');
    return recs?.[0] ?? null;
  });
  const [schedule, setSchedule] = useState<any[]>(() =>
    userId ? getCacheEntry<any[]>(`schedule:${userId}`) ?? [] : [],
  );
  const [loading, setLoading] = useState(() =>
    userId ? !dashboardHasWarmCache(userId) : true,
  );
  const [selectedCourse, setSelectedCourse] = useState<any>(null);
  const [reviewCourse, setReviewCourse] = useState<any>(null);

  useEffect(() => {
    if (!user) return;
    const fetchData = async () => {
      try {
        const [profileRes, recsRes, schedRes, roadmapRes] = await Promise.all([
          api.getProfile(user.user_id),
          api.getRecommendations(),
          api.getSchedule(user.user_id),
          api.getRoadmap(),
        ]);
        setProfile(profileRes.data);
        setRoadmapSummary(roadmapRes.data?.summary ?? null);
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

  const summary = roadmapSummary ?? {};
  const progressPercent = Math.min(summary.completion_pct ?? 0, 100);
  const passedCourses =
    (summary.passed_mandatory ?? 0) +
    (summary.passed_electives ?? 0) +
    (summary.passed_seminars ?? 0) +
    (summary.passed_generals ?? 0);
  // electives/seminars/generals_needed are "still remaining", not fixed totals
  // (electives have no fixed course count — see docs/ARCHITECTURE.md), so the
  // degree's total course count is passed-so-far + whatever's still needed.
  const totalCourses =
    (summary.total_mandatory ?? 0) +
    (summary.passed_electives ?? 0) + (summary.electives_needed ?? 0) +
    (summary.passed_seminars ?? 0) + (summary.seminars_needed ?? 0) +
    (summary.passed_generals ?? 0) + (summary.generals_needed ?? 0);

  return (
    <div className="w-full min-w-0 space-y-6 sm:space-y-8 animate-fade-in">
      <header>
        <h1 className="text-2xl sm:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">
          ברוך שובך, {user?.name}
        </h1>
        <p className="text-gray-500 mt-2">הנה סקירה של המצב האקדמי שלך.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Degree Progress Widget */}
        <div className="glass-panel col-span-1 flex flex-col items-center justify-center p-5 sm:p-6 hover:shadow-teal-500/20 transition-all">
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
              <span className="text-gray-800 font-medium">{passedCourses}</span> / {totalCourses} קורסים
            </p>
          </div>
        </div>

        {/* Recommendation Hero Section */}
        <div className="glass-panel col-span-1 lg:col-span-2 p-5 sm:p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -mr-16 -mt-16 transition-transform group-hover:scale-110"></div>
          
          <div className="relative z-10 h-full flex flex-col justify-between">
            <div>
              <div className="inline-block px-3 py-1 bg-yellow-500/20 text-yellow-500 rounded-full text-xs font-semibold mb-4 border border-yellow-500/30">
                #1 המלצה מובילה
              </div>
              {topRecommendation ? (
                <>
                  <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold mb-2">{topRecommendation.course.name}</h2>
                  <p className="text-gray-500 mb-4 line-clamp-2">{topRecommendation.explanation}</p>
                  
                  <div className="flex flex-wrap gap-2 sm:gap-4 mt-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                      ציון התאמה: {topRecommendation.score}%
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                      עומס: {topRecommendation.course.workload} שעות בשבוע
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
      <div className="glass-panel p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
          <h2 className="text-lg sm:text-xl font-semibold">ההעדפות שלך</h2>
          <Link to="/profile" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
            עריכת העדפות ←
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">שנת לימודים</div>
            <div className="font-medium text-lg">שנה {profile?.year_of_study || 1}</div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">תואר</div>
            <div className="font-medium text-lg truncate">{profile?.degree || 'מדעי המחשב'}</div>
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

      {/* My List */}
      <div className="glass-panel p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
          <h2 className="text-lg sm:text-xl font-semibold">הרשימה שלי</h2>
          <Link to="/explorer" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
            חיפוש קורסים ←
          </Link>
        </div>
        
        {schedule.length > 0 ? (
          <div className="space-y-3">
            {schedule.map((item, index) => (
              <div
                key={index}
                role="button"
                tabIndex={0}
                onClick={() => setSelectedCourse(item.course)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedCourse(item.course);
                  }
                }}
                className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center p-4 bg-gray-50 border border-gray-200 rounded-xl cursor-pointer hover:border-emerald-300 hover:bg-emerald-50/30 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-gray-800">{item.course.name}</h3>
                </div>
                <button 
                  type="button"
                  onClick={async (e) => {
                    e.stopPropagation();
                    if (!user) return;
                    await api.removeSchedule(user.user_id, item.course_code);
                    setSchedule(schedule.filter(s => s.course_code !== item.course_code));
                  }}
                  className="text-red-500 hover:text-red-600 text-sm font-medium sm:pr-4 sm:border-r sm:border-gray-200 sm:mr-4 self-end sm:self-center shrink-0"
                >
                  הסר
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 border border-gray-200 rounded-xl">
            <p className="text-gray-500 mb-4">עדיין לא הוספת קורסים להרשימה שלך.</p>
            <Link to="/recommendations" className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-medium transition-all shadow-md shadow-emerald-500/20">
              מצא קורסים
            </Link>
          </div>
        )}
      </div>

      {selectedCourse && (
        <CourseDetailModal
          course={selectedCourse}
          onClose={() => setSelectedCourse(null)}
          onOpenReviews={() => {
            setReviewCourse(selectedCourse);
            setSelectedCourse(null);
          }}
          showAddToList={false}
        />
      )}

      {reviewCourse && (
        <ReviewModal course={reviewCourse} onClose={() => setReviewCourse(null)} />
      )}
    </div>
  );
}
