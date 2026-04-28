import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

function ReviewModal({ course, onClose }: { course: any, onClose: () => void }) {
  const { user } = useAuth();
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || rating === 0) return;
    setSubmitting(true);
    try {
      await api.createCourseReview(course.course_code, user.user_id, {
        course_code: course.course_code,
        rating,
        review_text: reviewText
      });
      onClose();
    } catch (err) {
      console.error(err);
      alert('שגיאה בשליחת הביקורת');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-100 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-lg relative !p-8 shadow-[0_0_40px_rgba(168,85,247,0.3)]">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-800 transition-colors">✕</button>
        <h2 className="text-2xl font-bold mb-2">דרג את {course.name}</h2>
        <p className="text-gray-500 text-sm mb-6">שתף את החוויה שלך כדי לעזור לסטודנטים בעתיד.</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex flex-col items-center">
            <div className="flex gap-2 text-4xl cursor-pointer">
              {[1, 2, 3, 4, 5].map(star => (
                <span 
                  key={star}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={() => setRating(star)}
                  className={`transition-all hover:scale-110 ${(hoverRating || rating) >= star ? 'text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.8)]' : 'text-gray-400'}`}
                >
                  ★
                </span>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-500 mb-2">הביקורת שלך (רשות)</label>
            <textarea 
              value={reviewText}
              onChange={e => setReviewText(e.target.value)}
              placeholder="מה אהבת או לא אהבת בקורס? איך היה העומס?"
              className="w-full h-32 bg-gray-100 border border-gray-200 rounded-xl p-4 text-gray-800 placeholder-white/40 focus:outline-none focus:border-teal-400 focus:bg-gray-100 transition-all resize-none custom-scrollbar"
            ></textarea>
          </div>

          <button 
            type="submit" 
            disabled={submitting || rating === 0}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 py-3 rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(168,85,247,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'שולח...' : 'שלח ביקורת'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function CourseHistory() {
  const { user } = useAuth();
  const [history, setHistory] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewingCourse, setReviewingCourse] = useState<any>(null);

  useEffect(() => {
    if (user) {
      Promise.all([
        api.getHistory(user.user_id),
        api.getCourses()
      ]).then(([histRes, courseRes]) => {
        setHistory(histRes.data);
        setCourses(courseRes.data);
      }).catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [user, reviewingCourse]); // Refetch when modal closes to potentially show "Reviewed" state

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
    </div>
  );

  const completedCodes = new Set(history.map(h => h.course_code));

  const hasPrereqs = (prereqs: string) => {
    if (!prereqs) return true;
    const codes = prereqs.match(/\d{4,5}/g) || [];
    return codes.every(c => completedCodes.has(parseInt(c)));
  };

  // Group courses by level/year for the tree structure (simplified mock logic)
  const groupedCourses = [
    courses.filter(c => !c.prerequisites), // Level 1
    courses.filter(c => c.prerequisites && c.prerequisites.includes('10')), // Level 2 mock
    courses.filter(c => c.prerequisites && !c.prerequisites.includes('10')) // Level 3 mock
  ].filter(group => group.length > 0);

  return (
    <div className="space-y-8 animate-fade-in">
      <header className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-green-400 via-emerald-400 to-teal-500">My Academic Journey</h1>
        <p className="text-gray-500">Your personalized skill tree. Track your progress, unlock new courses, and share your experiences.</p>
      </header>

      <div className="glass-panel overflow-x-auto p-8 border border-gray-200 bg-gray-100">
        <div className="min-w-[800px] flex flex-col gap-16 relative">
          {groupedCourses.map((level, i) => (
            <div key={i} className="flex justify-center gap-8 relative z-10">
              {level.map(course => {
                const isCompleted = completedCodes.has(course.course_code);
                const isAvailable = !isCompleted && hasPrereqs(course.prerequisites);
                const isLocked = !isCompleted && !isAvailable;

                let cardStyle = "border-gray-200 bg-gray-100 opacity-50 grayscale"; // Locked
                if (isCompleted) {
                  cardStyle = "border-green-500/50 bg-green-500/10 shadow-[0_0_20px_rgba(34,197,94,0.2)]";
                } else if (isAvailable) {
                  cardStyle = "border-emerald-400 bg-blue-500/20 shadow-[0_0_20px_rgba(96,165,250,0.4)] hover:-translate-y-1 transition-transform cursor-pointer";
                }

                return (
                  <div key={course.course_code} className={`w-64 rounded-2xl p-5 border backdrop-blur-md flex flex-col relative ${cardStyle}`}>
                    {isLocked && (
                      <div className="absolute inset-0 flex items-center justify-center z-20">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-start mb-3">
                      <span className={`text-xs font-mono px-2 py-1 rounded ${isCompleted ? 'bg-green-500/20 text-green-300' : 'bg-gray-100 text-gray-500'}`}>
                        {course.course_code}
                      </span>
                      {isCompleted && <span className="text-xl">✅</span>}
                    </div>
                    
                    <h3 className={`font-bold mb-2 ${isLocked ? 'text-gray-400' : 'text-gray-800'}`}>{course.name}</h3>
                    
                    {isLocked && (
                      <p className="text-xs text-orange-300/70 mt-auto pt-2">Requires: {course.prerequisites}</p>
                    )}
                    
                    {isCompleted && (
                      <div className="mt-auto pt-4 border-t border-gray-200">
                        <button 
                          onClick={() => setReviewingCourse(course)}
                          className="w-full bg-gray-100 hover:bg-gray-100 text-gray-800 text-sm py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                          <span className="text-yellow-400">⭐</span> Rate Course
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {reviewingCourse && (
        <ReviewModal course={reviewingCourse} onClose={() => setReviewingCourse(null)} />
      )}
    </div>
  );
}
