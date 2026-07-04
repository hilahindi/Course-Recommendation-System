import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  courseModalOverlayClass,
  courseModalShellClass,
  CourseModalCloseButton,
  CourseModalHeader,
  CourseReviewsList,
  CourseReviewsSectionHeader,
  CourseSkillsPrerequisitesGrid,
  ReviewStarPicker,
} from './courseDetailUi';

export default function ReviewModal({ course, onClose }: { course: any; onClose: () => void }) {
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
        rating: newRating,
        review_text: newText,
        is_anonymous: isAnonymous,
      });
      // A student has at most one review per course, so replace any existing entry instead of appending.
      setReviews(prev => [res.data, ...prev.filter(r => r.student_id !== user.user_id)]);
      setNewText('');
    } catch (err) {
      console.error(err);
      alert('שגיאה בשליחת הביקורת');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={courseModalOverlayClass}>
      <div className={`${courseModalShellClass} custom-scrollbar`}>
        <CourseModalCloseButton onClose={onClose} />

        <CourseModalHeader course={course} />
        <CourseSkillsPrerequisitesGrid course={course} />

        <div>
          <CourseReviewsSectionHeader />

          <form onSubmit={handleSubmit} className="mb-4 rounded-xl border border-emerald-100 bg-emerald-50/40 p-4 space-y-3">
            <div>
              <label className="block text-xs text-emerald-700 mb-2 text-center">דירוג</label>
              <ReviewStarPicker value={newRating} onChange={setNewRating} />
            </div>

            <textarea
              required
              placeholder="שתף את החוויה שלך..."
              className="w-full bg-white border border-emerald-200 rounded-xl p-3 text-gray-800 focus:outline-none focus:border-emerald-500 text-sm min-h-[100px] resize-y"
              rows={4}
              value={newText}
              onChange={e => setNewText(e.target.value)}
            />

            <div className="flex flex-row items-center justify-between gap-3 flex-nowrap">
              <label className="inline-flex items-center gap-0.5 text-sm text-emerald-700 cursor-pointer whitespace-nowrap shrink-0 leading-none">
                <input
                  type="checkbox"
                  checked={isAnonymous}
                  onChange={e => setIsAnonymous(e.target.checked)}
                  className="w-3.5 h-3.5 rounded border-emerald-300 text-emerald-600 focus:ring-emerald-500 focus:ring-1 shrink-0 m-0"
                />
                <span className="pr-0.5">פרסם באנונימיות</span>
              </label>
              <button
                type="submit"
                disabled={submitting}
                className="text-sm bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded transition-colors shadow disabled:opacity-50 shrink-0 whitespace-nowrap"
              >
                {submitting ? 'מפרסם...' : 'פרסם ביקורת'}
              </button>
            </div>
          </form>

          <CourseReviewsList reviews={reviews} loading={loading} />
        </div>
      </div>
    </div>
  );
}
