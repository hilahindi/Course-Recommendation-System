const iconButtonClass =
  '!p-0 !m-0 !min-w-0 !shadow-none !transform-none hover:!transform-none border-0 focus:outline-none focus-visible:outline-none';

export const courseModalShellClass =
  'glass-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto relative !p-8 !bg-white backdrop-blur-none shadow-2xl border border-gray-200';

export const courseModalOverlayClass =
  'fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-gray-900/40 backdrop-blur-sm animate-fade-in';

const STAT_BOX_CLASS =
  'h-[4.5rem] w-full flex flex-col items-center justify-center rounded-xl border px-2 text-center';

function parsePrerequisiteItems(text: string): string[] {
  if (!text?.trim()) return [];
  return text.split(',').map(s => s.trim()).filter(Boolean);
}

export function CourseModalCloseButton({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      onClick={onClose}
      className={`absolute top-4 right-4 text-gray-400 hover:text-gray-800 bg-gray-100 hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-all ${iconButtonClass}`}
      aria-label="סגור"
    >
      ✕
    </button>
  );
}

export function CourseStatBox({
  label,
  value,
  sub,
  tone = 'emerald',
}: {
  label: string;
  value: string | number;
  sub?: string;
  tone?: 'emerald' | 'blue' | 'rose' | 'slate';
}) {
  const tones = {
    emerald: 'border-emerald-100 bg-emerald-50/60 text-emerald-800',
    blue: 'border-blue-100 bg-blue-50/60 text-blue-800',
    rose: 'border-rose-200 bg-rose-50 text-rose-800',
    slate: 'border-gray-200 bg-gray-50 text-gray-700',
  };
  return (
    <div className={`${STAT_BOX_CLASS} ${tones[tone]}`}>
      <div className="font-semibold opacity-80 text-[11px]">{label}</div>
      <div className="font-bold text-gray-900 leading-tight text-lg mt-0.5">{value}</div>
      {sub && <div className="text-gray-500 text-[10px] mt-0.5">{sub}</div>}
    </div>
  );
}

function PrerequisitesBox({ prerequisites }: { prerequisites: string }) {
  const items = parsePrerequisiteItems(prerequisites);
  if (items.length === 0) return null;

  return (
    <div className="min-h-[9rem] w-full flex flex-col items-center text-center rounded-xl border border-emerald-100 bg-emerald-50 p-4">
      <div className="font-semibold text-emerald-800 text-sm mb-2">דרישות קדם</div>
      <div className="flex flex-wrap gap-1.5 justify-center items-center">
        {items.map((item, i) => (
          <span
            key={`${item}-${i}`}
            className="inline-block rounded-lg border border-emerald-200 bg-white text-gray-700 text-xs px-2.5 py-1.5 leading-snug"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

export function CourseModalHeader({ course }: { course: any }) {
  return (
    <div className="mb-6 border-b border-gray-200 pb-6 text-center">
      <span className="inline-block bg-blue-500/20 px-3 py-1 rounded text-sm text-emerald-700 font-mono border border-blue-500/30 mb-3">
        {course.course_code}
      </span>
      <h2 className="text-2xl sm:text-3xl font-bold mb-4">{course.name}</h2>
      <div className="grid grid-cols-3 gap-3 max-w-sm mx-auto w-full">
        <CourseStatBox label='נ"ז' value={course.credits ?? '—'} tone="emerald" />
        <CourseStatBox label="שעות" value={course.workload ?? '—'} sub="בשבוע" tone="blue" />
        <CourseStatBox
          label="נוכחות"
          value={course.mandatory_attendance ? 'חובה' : 'גמישה'}
          tone={course.mandatory_attendance ? 'rose' : 'slate'}
        />
      </div>
    </div>
  );
}

export function CourseSkillsPrerequisitesGrid({ course }: { course: any }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      <div className="min-h-[9rem] rounded-xl border border-emerald-100 bg-emerald-50/40 p-4 flex flex-col items-center text-center">
        <h3 className="text-sm font-semibold text-emerald-700 mb-3">כישורים נרכשים</h3>
        {course.skills?.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 justify-center">
            {course.skills.map((s: any) => (
              <span
                key={s.id}
                className="inline-block rounded-lg border border-emerald-200 bg-white text-gray-700 text-xs px-2.5 py-1.5"
              >
                {s.name}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm italic text-center">לא צוינו כישורים ספציפיים.</p>
        )}
      </div>

      {course.prerequisites ? (
        <PrerequisitesBox prerequisites={course.prerequisites} />
      ) : (
        <div className="min-h-[9rem] rounded-xl border border-dashed border-gray-200 bg-gray-50 p-4 flex items-center justify-center text-sm text-gray-500 text-center">
          אין דרישות קדם לקורס זה
        </div>
      )}
    </div>
  );
}

export function CourseReviewCard({ review }: { review: any }) {
  return (
    <div className="bg-gray-100 rounded-xl p-4 border border-gray-200">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-yellow-400 text-sm leading-none">{'★'.repeat(review.rating)}</span>
        <span className="ml-auto text-xs text-emerald-600 font-medium">
          {review.student_name || `סטודנט #${review.student_id}`}
        </span>
      </div>
      <p className="text-sm text-gray-500">{review.review_text}</p>
    </div>
  );
}

export function ReviewStarPicker({
  value,
  onChange,
}: {
  value: number;
  onChange: (rating: number) => void;
}) {
  return (
    <div className="flex items-center justify-center gap-1">
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          type="button"
          onClick={() => onChange(star)}
          className={`${iconButtonClass} !bg-transparent text-3xl leading-none p-1 ${
            star <= value ? 'text-yellow-400' : 'text-gray-300'
          }`}
          aria-label={`${star} כוכבים`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

export function CourseReviewsList({
  reviews,
  loading,
}: {
  reviews: any[];
  loading: boolean;
}) {
  if (loading) {
    return <div className="text-center text-gray-400 text-sm">טוען ביקורות...</div>;
  }
  if (reviews.length === 0) {
    return (
      <div className="text-center text-gray-400 text-sm italic bg-gray-100 p-6 rounded-xl border border-gray-200">
        אין ביקורות עדיין. היה הראשון לכתוב!
      </div>
    );
  }
  return (
    <div className="space-y-4 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
      {reviews.map(review => (
        <CourseReviewCard key={review.id} review={review} />
      ))}
    </div>
  );
}

export function CourseReviewsActionsBar({
  course,
  onOpenReviews,
  onAddToList,
  showAddToList = true,
}: {
  course: any;
  onOpenReviews: () => void;
  onAddToList?: (course: any) => void;
  showAddToList?: boolean;
}) {
  return (
    <div
      className="flex justify-between items-center gap-3 mb-4 border-b border-emerald-500/20 pb-2"
      dir="rtl"
    >
      <h3 className="text-lg font-semibold text-emerald-700">ביקורות סטודנטים</h3>
      <div className="flex items-center gap-2 shrink-0">
        {showAddToList && onAddToList && (
          <button
            type="button"
            onClick={() => onAddToList(course)}
            className="text-sm bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded transition-colors shadow whitespace-nowrap"
          >
            הוסף להרשימה שלי
          </button>
        )}
        <button
          type="button"
          onClick={onOpenReviews}
          className="text-sm bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded transition-colors shadow whitespace-nowrap"
        >
          קרא / כתוב ביקורות
        </button>
      </div>
    </div>
  );
}

export function CourseReviewsSectionHeader({ title = 'ביקורות סטודנטים' }: { title?: string }) {
  return (
    <div className="flex justify-between items-center mb-4 border-b border-emerald-500/20 pb-2">
      <h3 className="text-lg font-semibold text-emerald-700">{title}</h3>
    </div>
  );
}
