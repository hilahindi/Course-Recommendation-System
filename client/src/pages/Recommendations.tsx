import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, getCacheEntry } from '../services/api';
import { Link } from 'react-router-dom';
import ReviewModal from '../components/ReviewModal';

function CourseRating({ onClick }: { courseCode: number; onClick: () => void }) {
  return (
    <button onClick={onClick} className="text-xs text-gray-500 hover:text-emerald-600 transition-colors bg-gray-50 px-2 py-1 border border-gray-200 rounded-full">
      דרג קורס
    </button>
  );
}

export default function Recommendations() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState<any[]>(
    () => getCacheEntry<any[]>('recommendations') ?? [],
  );
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(() => !getCacheEntry('recommendations'));
  const [error, setError] = useState<string | null>(null);
  const [reviewCourse, setReviewCourse] = useState<any>(null);

  const loadRecommendations = (force = false) => {
    setLoading(true);
    setError(null);
    return api
      .getRecommendations({ force })
      .then(res => setRecommendations(res.data))
      .catch(err => {
        console.error(err);
        const detail = err?.response?.data?.detail;
        setError(
          typeof detail === 'string'
            ? detail
            : 'לא הצלחנו לטעון המלצות. ודאי שהשרת רץ ושסיימת את תהליך ההצטרפות.'
        );
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    loadRecommendations();
  }, [user]);

  if (loading) {
    return (
      <div className="text-center mt-20 space-y-3 px-4">
        <p className="text-xl animate-pulse">מנתח את הפרופיל שלך...</p>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          מחשבים התאמה לתפקיד היעד שלך — זה עשוי לקחת כמה שניות.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel text-center p-12 max-w-lg mx-auto mt-12">
        <h2 className="text-2xl mb-4 text-red-600">שגיאה בטעינת ההמלצות</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          type="button"
          onClick={() => loadRecommendations(true)}
          className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-lg font-medium"
        >
          נסי שוב
        </button>
      </div>
    );
  }

  const activeRecommendations = recommendations.filter(r => !dismissed.has(r.course.course_code));

  const handleAdd = async (courseCode: number, courseName: string) => {
    if (!user) return;
    try {
      await api.addSchedule(user.user_id, { course_code: courseCode });
      alert(`"${courseName}" נוסף להרשימה שלך!`);
    } catch (e) {
      alert('שגיאה בהוספה להרשימה.');
    }
  };

  return (
    <div className="w-full min-w-0 space-y-6 sm:space-y-8 animate-fade-in">
      <div className="glass-panel text-center">
        <h1 className="text-2xl sm:text-3xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">
          המלצות חכמות
        </h1>
        <p className="text-gray-500 max-w-2xl mx-auto">
          בהתבסס על הקורסים שעברת ומטרות הקריירה, המערכת בנתה עבורך את המסלול המושלם.
        </p>
      </div>

      {activeRecommendations.length === 0 ? (
        <div className="glass-panel text-center p-12">
          {recommendations.length > 0 ? (
            <>
              <h2 className="text-2xl mb-4">עברת על כל ההמלצות</h2>
              <button 
                onClick={() => setDismissed(new Set())}
                className="bg-emerald-600 hover:bg-emerald-500 px-6 py-3 rounded-lg font-medium transition-all shadow-lg shadow-emerald-500/30"
              >
                אפס רשימה
              </button>
            </>
          ) : (
            <>
              <h2 className="text-2xl mb-4">לא נמצאו המלצות כרגע</h2>
              <p className="text-gray-500 mb-6">
                ודאי שבחרת תפקיד יעד בהצטרפות, ושיש קורסי בחירה שלא סיימת עדיין.
              </p>
              <div className="flex flex-wrap gap-3 justify-center">
                <button
                  type="button"
                  onClick={() => loadRecommendations(true)}
                  className="bg-emerald-600 hover:bg-emerald-500 px-6 py-3 rounded-lg font-medium transition-all shadow-lg shadow-emerald-500/30"
                >
                  רענן המלצות
                </button>
                <Link to="/profile" className="border border-gray-300 hover:border-emerald-400 px-6 py-3 rounded-lg font-medium transition-all">
                  עריכת פרופיל
                </Link>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="grid gap-6">
          {activeRecommendations.map((rec, index) => (
            <div key={rec.course.course_code} className="glass-panel relative overflow-hidden group border border-gray-200 hover:border-blue-500/30 transition-all p-4 sm:p-6">
              {/* Rank & Match Badge */}
              <div className="absolute top-0 right-0 flex">
                {index === 0 && (
                  <div className="bg-yellow-500/90 text-black font-bold py-1 px-3 shadow-lg flex items-center text-xs">
                    ⭐ בחירה מובילה
                  </div>
                )}
                <div className={`font-bold py-1 px-4 ${index === 0 ? 'bg-emerald-600 rounded-bl-xl' : 'bg-emerald-600/80 rounded-bl-xl shadow-lg'} text-gray-800 text-sm`}>
                  {rec.score}% התאמה
                </div>
              </div>
              
              <div className="flex flex-col md:flex-row gap-6 items-stretch mt-4 md:mt-0">
                <div className="flex-grow flex flex-col">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="bg-gray-100 px-2 py-1 rounded text-sm text-emerald-700 font-mono">
                      {rec.course.course_code}
                    </span>
                    <h2 className="text-2xl font-semibold">{rec.course.name}</h2>
                  </div>
                  
                  <div className="flex items-center gap-4 mb-4">
                    <CourseRating courseCode={rec.course.course_code} onClick={() => setReviewCourse(rec.course)} />
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    {rec.in_track_bundle && (
                      <span className="text-xs border border-emerald-300 bg-emerald-100 px-2 py-1 rounded-full text-emerald-800 font-medium">
                        במקבץ שלך
                      </span>
                    )}
                    {rec.prerequisites_met === false && rec.missing_prerequisites?.length > 0 && (
                      <span className="text-xs border border-amber-300 bg-amber-50 px-2 py-1 rounded-full text-amber-800">
                        דרישות קדם: {rec.missing_prerequisites.map((p: { name: string }) => p.name).join(', ')}
                      </span>
                    )}
                    <span className="text-xs border border-gray-200 bg-gray-100 px-2 py-1 rounded-full text-gray-500">
                      עומס: {rec.course.workload} שעות
                    </span>
                    <span className="text-xs border border-gray-200 bg-gray-100 px-2 py-1 rounded-full text-gray-500">
                      נוכחות: {rec.course.mandatory_attendance ? 'חובה' : 'גמיש'}
                    </span>
                  </div>
                  
                  {rec.course.skills?.length > 0 && (
                    <div className="mb-4 flex flex-wrap gap-2">
                      <span className="text-xs text-gray-400 my-auto ml-1">כישורים נרכשים:</span>
                      {rec.course.skills.map((s: any) => (
                        <span key={s.id} className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full border border-emerald-200">
                          {s.name}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-auto flex gap-3 pt-4">
                    <button 
                      onClick={() => handleAdd(rec.course.course_code, rec.course.name)}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-md shadow-emerald-500/20"
                    >
                      הוסף להרשימה שלי
                    </button>
                  </div>
                </div>

                <div className="md:w-1/3 w-full bg-emerald-50/30 border border-emerald-400/20 rounded-xl p-5 flex flex-col justify-center relative overflow-hidden group-hover:bg-emerald-50/50 transition-colors">
                  <div className="absolute -right-4 -top-4 w-16 h-16 bg-blue-500/20 rounded-full blur-xl"></div>
                  <h3 className="text-sm text-emerald-700 font-semibold mb-3 uppercase tracking-wider flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    למה הקורס הזה?
                  </h3>
                  <p className="text-gray-700 text-sm leading-relaxed mb-3 whitespace-pre-line">
                    {rec.explanation}
                  </p>
                  {rec.matching_skills?.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {rec.matching_skills.map((skill: string) => (
                        <span
                          key={skill}
                          className="text-xs bg-white/80 text-emerald-800 px-2 py-1 rounded-full border border-emerald-300"
                        >
                          {skill.trim()}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-xs">אין חפיפת כישורים ישירה עם השוק.</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {reviewCourse && (
        <ReviewModal course={reviewCourse} onClose={() => setReviewCourse(null)} />
      )}
    </div>
  );
}
