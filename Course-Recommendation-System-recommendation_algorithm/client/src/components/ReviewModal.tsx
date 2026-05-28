import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function ReviewModal({ course, onClose }: { course: any, onClose: () => void }) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [newRating, setNewRating] = useState(5);
  const [newText, setNewText] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getCourseReviews(course.course_code)
      .then(res => setReviews(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [course.course_code]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    try {
      const res = await api.createCourseReview(course.course_code, user.user_id, {
        course_code: course.course_code,
        rating: newRating,
        review_text: newText,
        is_anonymous: isAnonymous
      });
      setReviews(prev => [res.data, ...prev.filter(r => r.student_id !== user.user_id)]);
      setNewText('');
    } catch (err) {
      console.error(err);
      alert("שגיאה בשליחת הביקורת");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 sm:p-6">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl animate-fade-in max-h-[90vh] flex flex-col min-h-0">
        <div className="flex justify-between items-start gap-4 mb-6 border-b pb-4 shrink-0">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold text-gray-800 break-words">{course.name}</h2>
            <p className="text-sm text-emerald-600 font-mono">קוד קורס: {course.course_code}</p>
          </div>
          <button type="button" onClick={onClose} className="shrink-0 text-gray-400 hover:text-gray-600 text-xl leading-none p-1" aria-label="סגור">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-6 min-h-0">
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="font-semibold text-emerald-800">כתוב ביקורת</h3>

            <div className="w-full">
              <label className="block text-xs text-emerald-700 mb-1.5">דירוג</label>
              <div className="bg-emerald-50 rounded-xl px-4 py-3 border border-emerald-100 w-full">
                <div className="flex justify-between w-full">
                  {[1, 2, 3, 4, 5].map(star => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setNewRating(star)}
                      className={`text-2xl leading-none ${star <= newRating ? 'text-yellow-400' : 'text-gray-300'}`}
                      aria-label={`${star} כוכבים`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <textarea
              required
              placeholder="שתף את החוויה שלך..."
              className="w-full bg-white border border-emerald-200 rounded-lg p-3 text-gray-800 focus:outline-none focus:border-emerald-500 text-sm min-h-[100px] resize-y"
              rows={4}
              value={newText}
              onChange={e => setNewText(e.target.value)}
            />
            <div className="flex flex-wrap justify-between items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-emerald-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAnonymous}
                  onChange={e => setIsAnonymous(e.target.checked)}
                  className="rounded text-emerald-600 focus:ring-emerald-500 bg-white border-emerald-300"
                />
                פרסם באנונימיות
              </label>
              <button
                type="submit"
                disabled={submitting}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium shadow disabled:opacity-50"
              >
                {submitting ? 'מפרסם...' : 'פרסם ביקורת'}
              </button>
            </div>
          </form>

          <div>
            <h3 className="font-semibold text-gray-800 mb-4">ביקורות סטודנטים</h3>
            {loading ? (
              <div className="text-gray-500 text-sm">טוען ביקורות...</div>
            ) : reviews.length === 0 ? (
              <div className="text-gray-500 text-sm italic">אין עדיין ביקורות. היה הראשון לכתוב!</div>
            ) : (
              <div className="space-y-3">
                {reviews.map(r => (
                  <div key={r.id} className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="min-w-0">
                        <span className="font-semibold text-gray-800 text-sm break-words">{r.student_name}</span>
                        <div className="text-yellow-400 text-xs mt-0.5">
                          {'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}
                        </div>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm leading-relaxed break-words whitespace-pre-wrap">{r.review_text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
