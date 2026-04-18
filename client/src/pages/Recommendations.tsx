import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

function CourseRating({ courseCode }: { courseCode: number }) {
  const [rating, setRating] = useState<number | null>(null);
  const [count, setCount] = useState(0);

  useEffect(() => {
    api.getCourseReviews(courseCode).then(res => {
      const reviews = res.data;
      if (reviews.length > 0) {
        const avg = reviews.reduce((acc: number, r: any) => acc + r.rating, 0) / reviews.length;
        setRating(avg);
        setCount(reviews.length);
      }
    }).catch(console.error);
  }, [courseCode]);

  if (rating === null) return <div className="text-xs text-white/50">No reviews yet</div>;

  return (
    <div className="flex items-center gap-1 text-sm">
      <span className="text-yellow-400">⭐</span>
      <span className="font-medium text-white">{rating.toFixed(1)}/5</span>
      <span className="text-white/50 text-xs">({count} reviews)</span>
    </div>
  );
}

export default function Recommendations() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      api.getRecommendations(user.user_id)
        .then(res => setRecommendations(res.data))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [user]);

  if (loading) {
    return <div className="text-center mt-20 text-xl animate-pulse">Analyzing your profile...</div>;
  }

  const activeRecommendations = recommendations.filter(r => !dismissed.has(r.course.course_code));

  const handleDismiss = (courseCode: number) => {
    setDismissed(prev => {
      const newSet = new Set(prev);
      newSet.add(courseCode);
      return newSet;
    });
  };

  const handleAdd = async (courseCode: number) => {
    // Ideally this would add to a "Planned Courses" table
    alert(`Course ${courseCode} added to your semester!`);
    handleDismiss(courseCode);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="glass-panel text-center">
        <h1 className="text-3xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
          Smart Recommendations
        </h1>
        <p className="text-white/70 max-w-2xl mx-auto">
          Based on your past courses, workload capacity, and career goals, our AI has curated the perfect path forward for you.
        </p>
      </div>

      {activeRecommendations.length === 0 ? (
        <div className="glass-panel text-center p-12">
          {recommendations.length > 0 ? (
            <>
              <h2 className="text-2xl mb-4">You've reviewed all recommendations</h2>
              <button 
                onClick={() => setDismissed(new Set())}
                className="bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/30"
              >
                Reset List
              </button>
            </>
          ) : (
            <>
              <h2 className="text-2xl mb-4">We need more information</h2>
              <p className="text-white/60 mb-6">Take the preference questionnaire to get personalized recommendations.</p>
              <Link to="/questionnaire" className="bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/30">
                Start Questionnaire
              </Link>
            </>
          )}
        </div>
      ) : (
        <div className="grid gap-6">
          {activeRecommendations.map((rec, index) => (
            <div key={rec.course.course_code} className="glass-panel relative overflow-hidden group border border-white/5 hover:border-blue-500/30 transition-all">
              {/* Rank & Match Badge */}
              <div className="absolute top-0 right-0 flex">
                {index === 0 && (
                  <div className="bg-yellow-500/90 text-black font-bold py-1 px-3 shadow-lg flex items-center text-xs">
                    ⭐ #1 Selection
                  </div>
                )}
                <div className={`font-bold py-1 px-4 ${index === 0 ? 'bg-blue-600 rounded-bl-xl' : 'bg-blue-600/80 rounded-bl-xl shadow-lg'} text-white text-sm`}>
                  {rec.score}% Match
                </div>
              </div>
              
              <div className="flex flex-col md:flex-row gap-6 items-stretch mt-4 md:mt-0">
                <div className="flex-grow flex flex-col">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="bg-white/10 px-2 py-1 rounded text-sm text-blue-300 font-mono">
                      {rec.course.course_code}
                    </span>
                    <h2 className="text-2xl font-semibold">{rec.course.name}</h2>
                  </div>
                  
                  <div className="flex items-center gap-4 mb-4">
                    <CourseRating courseCode={rec.course.course_code} />
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="text-xs border border-white/20 bg-black/20 px-2 py-1 rounded-full text-white/70">
                      Workload: {rec.course.workload} hrs
                    </span>
                    <span className="text-xs border border-white/20 bg-black/20 px-2 py-1 rounded-full text-white/70">
                      Attendance: {rec.course.mandatory_attendance ? 'Mandatory' : 'Flexible'}
                    </span>
                  </div>
                  
                  {rec.course.skills?.length > 0 && (
                    <div className="mb-4 flex flex-wrap gap-2">
                      <span className="text-xs text-white/50 my-auto mr-1">Skills Gained:</span>
                      {rec.course.skills.map((s: any) => (
                        <span key={s.id} className="text-xs bg-purple-500/20 text-purple-200 px-2 py-1 rounded-full border border-purple-500/30">
                          {s.name}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-auto flex gap-3 pt-4">
                    <button 
                      onClick={() => handleAdd(rec.course.course_code)}
                      className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-[0_0_10px_rgba(37,99,235,0.3)]"
                    >
                      Add to My Semester
                    </button>
                    <button 
                      onClick={() => handleDismiss(rec.course.course_code)}
                      className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                      Not Interested
                    </button>
                  </div>
                </div>

                <div className="md:w-1/3 w-full bg-blue-900/10 border border-blue-400/20 rounded-xl p-5 flex flex-col justify-center relative overflow-hidden group-hover:bg-blue-900/20 transition-colors">
                  <div className="absolute -right-4 -top-4 w-16 h-16 bg-blue-500/20 rounded-full blur-xl"></div>
                  <h3 className="text-sm text-blue-300 font-semibold mb-3 uppercase tracking-wider flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    Why this course?
                  </h3>
                  <p className="text-white/90 text-sm leading-relaxed italic">
                    "{rec.explanation}"
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
