import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

function ReviewModal({ course, onClose }: { course: any; onClose: () => void }) {
  const { user } = useAuth();
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (!user || rating === 0) return;
    setSubmitting(true);
    try {
      await api.createCourseReview(course.code, user.user_id, {
        rating,
        review_text: reviewText,
      });
      onClose();
    } catch {
      alert('שגיאה בשליחת הביקורת');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-lg relative !p-8">
        <button onClick={onClose} className="absolute top-4 left-4 text-gray-400 hover:text-gray-800 transition-colors text-xl">✕</button>
        <h2 className="text-xl font-bold mb-1 text-right">{course.name}</h2>
        <p className="text-gray-500 text-sm mb-6 text-right">שתף את החוויה שלך כדי לעזור לסטודנטים אחרים</p>
        <form onSubmit={handleSubmit} className="space-y-5" dir="rtl">
          <div className="flex gap-2 text-4xl cursor-pointer justify-center">
            {[1, 2, 3, 4, 5].map(star => (
              <span
                key={star}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(star)}
                className={`transition-all hover:scale-110 ${(hoverRating || rating) >= star ? 'text-yellow-400' : 'text-gray-300'}`}
              >★</span>
            ))}
          </div>
          <textarea
            value={reviewText}
            onChange={e => setReviewText(e.target.value)}
            placeholder="מה אהבת? מה היה קשה? איך היה העומס?"
            className="w-full h-28 bg-gray-50 border border-gray-200 rounded-xl p-4 text-gray-800 placeholder-gray-400 focus:outline-none focus:border-emerald-400 transition-all resize-none"
          />
          <button
            type="submit"
            disabled={submitting || rating === 0}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'שולח...' : 'שלח ביקורת'}
          </button>
        </form>
      </div>
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  passed: 'border-emerald-400 bg-emerald-50',
  upcoming: 'border-gray-200 bg-gray-50 opacity-70',
  recommended: 'border-teal-400 bg-teal-50',
};

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  passed: { label: '✅ הושלם', cls: 'bg-emerald-100 text-emerald-700' },
  upcoming: { label: '🔒 עתידי', cls: 'bg-gray-100 text-gray-500' },
  recommended: { label: '⭐ מומלץ', cls: 'bg-teal-100 text-teal-700' },
};

const CATEGORY_LABEL: Record<string, string> = {
  mandatory: 'חובה',
  elective: 'בחירה',
  elective1: 'בחירה',
  seminar: 'סמינר',
};

export default function CourseHistory() {
  const { user } = useAuth();
  const [roadmap, setRoadmap] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewingCourse, setReviewingCourse] = useState<any>(null);

  const fetchRoadmap = () => {
    if (!user) return;
    setLoading(true);
    api.getRoadmap()
      .then(res => setRoadmap(res.data))
      .catch(() => setError('לא ניתן לטעון את מפת הדרכים'))
      .finally(() => setLoading(false));
  };

  useEffect(fetchRoadmap, [user]);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500" />
    </div>
  );

  if (error) return (
    <div className="text-center py-20 text-gray-500">
      <p className="mb-4">{error}</p>
      <button onClick={fetchRoadmap} className="text-emerald-600 underline">נסה שוב</button>
    </div>
  );

  const { semesters = [], summary = {} } = roadmap || {};
  const completion = summary.completion_pct ?? 0;

  return (
    <div className="w-full min-w-0 space-y-6 sm:space-y-8 animate-fade-in" dir="rtl">

      {/* Header */}
      <div className="glass-panel text-center">
        <h1 className="text-2xl sm:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500 mb-2">
          המסע האקדמי שלי
        </h1>
        <p className="text-gray-500 text-sm">מפת דרכים לסיום התואר — חובות, בחירה חופשית וקורסים מומלצים</p>

        {/* Progress bar */}
        <div className="mt-5 mb-3">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>{completion}% הושלם</span>
            <span>{summary.passed_mandatory ?? 0}/{summary.total_mandatory ?? 0} חובה</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-emerald-500 to-teal-400 h-3 rounded-full transition-all duration-700"
              style={{ width: `${completion}%` }}
            />
          </div>
        </div>

        {/* Stats row */}
        <div className="flex justify-center gap-6 mt-4 text-sm flex-wrap">
          <div className="text-center">
            <div className="font-bold text-emerald-600 text-lg">{summary.passed_mandatory ?? 0}/{summary.total_mandatory ?? 0}</div>
            <div className="text-gray-500">קורסי חובה</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-teal-600 text-lg">{summary.passed_electives ?? 0}/{summary.electives_needed ?? 0}</div>
            <div className="text-gray-500">בחירה חופשית</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-blue-600 text-lg">{summary.passed_seminars ?? 0}/{summary.seminars_needed ?? 0}</div>
            <div className="text-gray-500">סמינריון</div>
          </div>
        </div>
      </div>

      {/* Semesters */}
      {semesters.map((sem: any) => (
        <div key={sem.number} className="glass-panel">
          <h2 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 text-sm flex items-center justify-center font-mono">
              {sem.number}
            </span>
            {sem.label}
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {sem.courses.map((course: any) => {
              const badge = STATUS_BADGE[course.status] ?? STATUS_BADGE.upcoming;
              const cardCls = STATUS_STYLES[course.status] ?? STATUS_STYLES.upcoming;

              return (
                <div
                  key={course.code}
                  className={`rounded-xl border p-4 flex flex-col gap-2 transition-all ${cardCls}`}
                >
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-mono text-gray-400">{course.code}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>
                      {badge.label}
                    </span>
                  </div>

                  <p className="font-semibold text-gray-800 text-sm leading-snug">{course.name}</p>

                  <div className="flex justify-between items-center mt-auto pt-1">
                    <span className="text-xs text-gray-400">
                      {CATEGORY_LABEL[course.category] ?? course.category} · {course.credits} נ״ז
                    </span>
                    {course.status === 'passed' && (
                      <button
                        onClick={() => setReviewingCourse(course)}
                        className="text-xs text-emerald-600 hover:text-emerald-700 font-medium underline"
                      >
                        דרג
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {reviewingCourse && (
        <ReviewModal
          course={reviewingCourse}
          onClose={() => { setReviewingCourse(null); fetchRoadmap(); }}
        />
      )}
    </div>
  );
}
