import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, getCacheEntry } from '../services/api';
import Select from 'react-select';
import ReviewModal from '../components/ReviewModal';

type HistoryEntry = {
  id?: number;
  course_code: number;
  grade: number | '';
  course?: { name: string };
};

function entryIsUnsaved(entry: HistoryEntry, savedHistory: HistoryEntry[]): boolean {
  if (entry.id == null) return true;
  const saved = savedHistory.find(s => s.course_code === entry.course_code);
  return saved == null || saved.grade !== entry.grade;
}

const STATUS_STYLES: Record<string, string> = {
  passed: 'border-emerald-500 bg-emerald-100 ring-1 ring-emerald-200/80',
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

const MANDATORY_YEAR_LABELS: Record<number, string> = {
  1: "א'",
  2: "ב'",
  3: "ג'",
};

export default function CourseHistory() {
  const { user } = useAuth();
  const userId = user?.user_id;
  const [roadmap, setRoadmap] = useState<any>(() => getCacheEntry('roadmap'));
  const [loading, setLoading] = useState(() => {
    if (!userId) return true;
    return !(
      getCacheEntry('roadmap') &&
      getCacheEntry('courses') &&
      getCacheEntry(`history:${userId}`) &&
      getCacheEntry('yearly-mandatory')
    );
  });
  const [error, setError] = useState<string | null>(null);
  const [reviewingCourse, setReviewingCourse] = useState<any>(null);

  const [courses, setCourses] = useState<any[]>(() => getCacheEntry('courses') ?? []);
  const [history, setHistory] = useState<HistoryEntry[]>(() =>
    userId ? getCacheEntry<HistoryEntry[]>(`history:${userId}`) ?? [] : [],
  );
  const [savedHistory, setSavedHistory] = useState<HistoryEntry[]>(() =>
    userId ? getCacheEntry<HistoryEntry[]>(`history:${userId}`) ?? [] : [],
  );
  const [yearlyCoursesMap, setYearlyCoursesMap] = useState<Record<number, number[]>>(
    () => getCacheEntry('yearly-mandatory') ?? {},
  );
  const [selectedCourse, setSelectedCourse] = useState<number | ''>('');
  const [grade, setGrade] = useState('');
  const [historySaving, setHistorySaving] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [showHistoryEditor, setShowHistoryEditor] = useState(false);

  const fetchRoadmap = useCallback((force = false) => {
    if (!user) return Promise.resolve();
    return api.getRoadmap({ force })
      .then(res => setRoadmap(res.data))
      .catch(() => setError('לא ניתן לטעון את מפת הדרכים'));
  }, [user]);

  const fetchHistoryData = useCallback((force = false) => {
    if (!user) return Promise.resolve();
    return Promise.all([
      api.getHistory(user.user_id, { force }),
      api.getCourses({ force }),
      api.getYearlyMandatoryCourses({ force }),
    ])
      .then(([historyRes, coursesRes, yearlyRes]) => {
        const saved: HistoryEntry[] = historyRes.data.map((h: HistoryEntry) => ({
          id: h.id,
          course_code: h.course_code,
          grade: h.grade,
          course: h.course,
        }));
        setSavedHistory(saved);
        setHistory(prev => {
          const drafts = prev.filter(h => entryIsUnsaved(h, saved));
          const savedCodes = new Set(saved.map(s => s.course_code));
          const keptDrafts = drafts.filter(d => !savedCodes.has(d.course_code));
          return [...saved, ...keptDrafts];
        });
        setYearlyCoursesMap(yearlyRes.data);
        setCourses(coursesRes.data);
      })
      .catch(() => setHistoryError('לא ניתן לטעון את היסטוריית הקורסים'));
  }, [user]);

  const refreshAll = useCallback((force = false) => {
    if (!user) return;
    setLoading(true);
    setError(null);
    Promise.all([fetchRoadmap(force), fetchHistoryData(force)])
      .finally(() => setLoading(false));
  }, [user, fetchRoadmap, fetchHistoryData]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const historyCourseCodes = new Set(history.map(h => h.course_code));
  const availableCourseOptions = courses.filter(
    c => !historyCourseCodes.has(c.course_code)
  );

  const currentCodes = new Set(history.map(h => h.course_code));
  const hasPendingChanges =
    savedHistory.some(s => !currentCodes.has(s.course_code)) ||
    history.some(h => entryIsUnsaved(h, savedHistory));

  const handleAddHistory = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedCourse === '') return;
    const courseCode = Number(selectedCourse);

    let numericGrade: number | '' = '';
    if (grade !== '') {
      const parsed = parseInt(grade, 10);
      if (Number.isNaN(parsed) || parsed < 0 || parsed > 100) {
        setHistoryError('יש להזין ציון בין 0 ל-100');
        return;
      }
      numericGrade = parsed;
    }

    const course = courses.find(c => c.course_code === courseCode);
    setHistory(prev => [
      ...prev,
      {
        course_code: courseCode,
        grade: numericGrade,
        course: course ? { name: course.name } : undefined,
      },
    ]);
    setSelectedCourse('');
    setGrade('');
    setHistoryError(null);
  };

  const handleRemoveHistory = (courseCode: number) => {
    setHistory(prev => prev.filter(h => h.course_code !== courseCode));
    setHistoryError(null);
  };

  const handleSaveAll = async () => {
    if (!user) return;

    const missingGrade = history.filter(h => h.grade === '');
    if (missingGrade.length > 0) {
      setHistoryError('יש להזין ציון לכל הקורסים לפני שמירה');
      return;
    }

    setHistorySaving(true);
    setHistoryError(null);
    try {
      const toDelete = savedHistory.filter(s => !currentCodes.has(s.course_code));
      const toUpsert = history.filter(h => entryIsUnsaved(h, savedHistory));

      await Promise.all(
        toDelete.map(s => api.deleteHistory(user.user_id, s.course_code))
      );

      if (toUpsert.length > 0) {
        await api.addHistoryBulk(user.user_id, {
          courses: toUpsert.map(h => ({
            course_code: h.course_code,
            grade: h.grade as number,
          })),
        });
      }

      await Promise.all([fetchHistoryData(true), fetchRoadmap(true)]);
    } catch {
      setHistoryError('שגיאה בשמירה. נסי שוב.');
    } finally {
      setHistorySaving(false);
    }
  };

  const handleAutoFill = (year: number) => {
    const knownCodes = new Set(courses.map(c => c.course_code));
    const existingCodes = new Set(history.map(h => h.course_code));
    const toAdd = (yearlyCoursesMap[year] || []).filter(
      code => knownCodes.has(code) && !existingCodes.has(code)
    );

    if (toAdd.length === 0) return;

    setHistory(prev => [
      ...prev,
      ...toAdd.map(code => {
        const course = courses.find(c => c.course_code === code);
        return {
          course_code: code,
          grade: '' as const,
          course: course ? { name: course.name } : undefined,
        };
      }),
    ]);
  };

  const mandatoryYearButtons = ([1, 2, 3] as const).filter(
    year => (yearlyCoursesMap[year]?.length ?? 0) > 0
  );

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500" />
    </div>
  );

  if (error) return (
    <div className="text-center py-20 text-gray-500">
      <p className="mb-4">{error}</p>
      <button onClick={refreshAll} className="text-emerald-600 underline">נסה שוב</button>
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
            <div className="text-gray-500">סמינר</div>
          </div>
        </div>

      </div>

      {/* Add completed courses */}
      <div className="glass-panel">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-lg font-bold text-gray-800">קורסים שעברתי</h2>
          <button
            type="button"
            onClick={() => setShowHistoryEditor(v => !v)}
            className="text-sm font-medium text-emerald-700 border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 px-4 py-2 rounded-lg transition-colors"
          >
            {showHistoryEditor ? 'הסתר' : history.length === 0 ? 'הוסף קורסים' : 'ערוך קורסים'}
          </button>
        </div>

        {!showHistoryEditor && history.length > 0 && (
          <p className="text-sm text-gray-600">
            {history.length} קורסים רשומים.
          </p>
        )}

        {showHistoryEditor && (
          <div className="space-y-4 mt-2">
            {mandatoryYearButtons.length > 0 && (
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                <p className="text-xs text-blue-700 mb-3 font-medium">הוסף קורסי חובה לפי שנה</p>
                <div className="flex gap-2 flex-wrap">
                  {mandatoryYearButtons.map(year => (
                    <button
                      key={year}
                      type="button"
                      disabled={historySaving}
                      onClick={() => handleAutoFill(year)}
                      className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg transition-colors"
                    >
                      קורסי חובה שנה {MANDATORY_YEAR_LABELS[year]}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <form
              onSubmit={handleAddHistory}
              className="bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-col sm:flex-row sm:items-end gap-3 w-full"
            >
              <div className="flex flex-col flex-1 min-w-0 text-right">
                <label className="text-xs text-gray-600 mb-1.5 mr-1 font-medium">חפש או בחר קורס</label>
                <Select
                  className="text-sm"
                  placeholder="הקלד שם או מספר קורס..."
                  options={availableCourseOptions.map(c => ({
                    value: c.course_code,
                    label: `${c.course_code} - ${c.name}`,
                  }))}
                  value={
                    selectedCourse === ''
                      ? null
                      : availableCourseOptions
                          .map(c => ({ value: c.course_code, label: `${c.course_code} - ${c.name}` }))
                          .find(o => o.value === selectedCourse) ?? null
                  }
                  onChange={(selected: { value: number } | null) =>
                    setSelectedCourse(selected ? selected.value : '')
                  }
                  isSearchable
                  isClearable
                  isDisabled={historySaving}
                  noOptionsMessage={() => 'לא נמצאו קורסים'}
                  styles={{
                    control: base => ({
                      ...base,
                      borderRadius: '0.5rem',
                      borderColor: '#D1D5DB',
                      minHeight: '40px',
                      boxShadow: 'none',
                      '&:hover': { borderColor: '#34D399' },
                    }),
                  }}
                />
              </div>

              <div className="flex flex-col w-full sm:w-24 text-right shrink-0">
                <label className="text-xs text-gray-600 mb-1.5 mr-1 font-medium">ציון</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  placeholder="0-100"
                  value={grade}
                  onChange={e => setGrade(e.target.value)}
                  disabled={historySaving}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 h-10 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 m-0 box-border"
                />
              </div>

              <button
                type="submit"
                disabled={selectedCourse === ''}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium px-6 h-10 rounded-lg disabled:opacity-50 transition-colors whitespace-nowrap shrink-0"
              >
                הוסף
              </button>
            </form>

            {history.length > 0 && (
              <div className="border border-gray-100 rounded-xl overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 flex justify-between items-center text-sm font-semibold text-gray-600 border-b border-gray-100">
                  <span>קורס</span>
                  <span>ציון</span>
                </div>
                <div className="max-h-60 overflow-y-auto custom-scrollbar divide-y divide-gray-100">
                  {history.map(entry => {
                    const name =
                      entry.course?.name ??
                      courses.find(c => c.course_code === entry.course_code)?.name ??
                      'קורס לא ידוע';
                    const unsaved = entryIsUnsaved(entry, savedHistory);
                    const isNew = entry.id == null;
                    const hasGrade = entry.grade !== '';
                    const passed = !unsaved && hasGrade && entry.grade >= 60;
                    const failed = !unsaved && hasGrade && entry.grade < 60;
                    return (
                      <div
                        key={entry.course_code}
                        className={`flex justify-between items-center p-3 px-4 transition-colors gap-3 ${
                          unsaved
                            ? 'bg-sky-50 hover:bg-sky-100/70 border-s-4 border-s-sky-400'
                            : passed
                              ? 'bg-emerald-50 hover:bg-emerald-100/80'
                              : failed
                                ? 'bg-amber-50/60 hover:bg-amber-50'
                                : 'bg-white hover:bg-gray-50'
                        }`}
                      >
                        <div className="min-w-0 text-right">
                          <span className={`font-mono font-medium ml-2 ${
                            unsaved ? 'text-sky-700' : passed ? 'text-emerald-700' : 'text-gray-500'
                          }`}>
                            {entry.course_code}
                          </span>
                          <span className={`text-sm ${
                            unsaved ? 'text-sky-900 font-medium' : passed ? 'text-emerald-900 font-medium' : 'text-gray-800'
                          }`}>{name}</span>
                          {unsaved && (
                            <span className="mr-2 text-xs font-medium text-sky-600">
                              {isNew ? '(חדש)' : '(עודכן)'}
                            </span>
                          )}
                          {failed && (
                            <span className="mr-2 text-xs text-amber-700">(לא עבר)</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <input
                            type="number"
                            min={0}
                            max={100}
                            placeholder="ציון"
                            value={entry.grade}
                            disabled={historySaving}
                            onChange={e => {
                              const val = e.target.value;
                              setHistory(prev =>
                                prev.map(h =>
                                  h.course_code === entry.course_code
                                    ? { ...h, grade: val === '' ? '' : Number(val) }
                                    : h
                                )
                              );
                            }}
                            className={`w-16 text-center border rounded-lg p-1.5 text-sm font-semibold focus:outline-none focus:border-emerald-400 ${
                              entry.grade === ''
                                ? 'border-amber-300 bg-amber-50 text-amber-800'
                                : unsaved
                                  ? 'border-sky-300 bg-white text-sky-800'
                                  : passed
                                    ? 'border-emerald-300 bg-white text-emerald-800'
                                    : 'border-gray-200 bg-white text-gray-700'
                            }`}
                          />
                          <button
                            type="button"
                            disabled={historySaving}
                            onClick={() => handleRemoveHistory(entry.course_code)}
                            className="text-red-500 hover:bg-red-50 p-2 rounded-md transition-colors"
                            aria-label="הסר קורס"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex flex-col items-end gap-2 pt-3 border-t border-gray-100">
              {historyError && (
                <p className="text-sm text-red-600 w-full text-right">{historyError}</p>
              )}
              <button
                type="button"
                disabled={historySaving || !hasPendingChanges}
                onClick={handleSaveAll}
                className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-semibold px-8 py-2.5 rounded-lg transition-colors shadow-sm"
              >
                {historySaving ? 'שומר...' : 'שמור'}
              </button>
            </div>
          </div>
        )}
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
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-xs font-mono text-gray-400">{course.code}</span>
                    <div className="flex flex-wrap gap-1 justify-end">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>
                        {badge.label}
                      </span>
                    </div>
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
          course={{
            name: reviewingCourse.name,
            course_code: reviewingCourse.code ?? reviewingCourse.course_code,
          }}
          onClose={() => { setReviewingCourse(null); refreshAll(); }}
        />
      )}
    </div>
  );
}
