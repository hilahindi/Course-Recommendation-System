import { useState, useEffect, useMemo } from 'react';
import { api, getCacheEntry } from '../services/api';
import { useAuth } from '../context/AuthContext';
import ReviewModal from '../components/ReviewModal';
import CourseDetailModal from '../components/CourseDetailModal';

function parsePrerequisiteItems(text: string): string[] {
  if (!text?.trim()) return [];
  return text.split(',').map((s) => s.trim()).filter(Boolean);
}

const PASSING_GRADE = 60;

function codeVariants(code: number): number[] {
  const variants = [code];
  if (code >= 100000) variants.push(code % 100000);
  return variants;
}

function codeInPassed(code: number, passed: Set<number>): boolean {
  return codeVariants(code).some(v => passed.has(v));
}

function buildPassedCodes(historyEntries: { course_code: number; grade: number }[]): Set<number> {
  const passed = new Set<number>();
  for (const entry of historyEntries) {
    if (entry.grade < PASSING_GRADE) continue;
    for (const variant of codeVariants(entry.course_code)) {
      passed.add(variant);
    }
  }
  return passed;
}

function buildCourseNameIndex(courses: { course_code: number; name: string }[]): Map<string, number[]> {
  const map = new Map<string, number[]>();
  for (const course of courses) {
    const key = course.name.trim();
    const codes = map.get(key) ?? [];
    codes.push(course.course_code);
    map.set(key, codes);
  }
  return map;
}

function prereqNameSatisfied(
  name: string,
  passed: Set<number>,
  nameToCodes: Map<string, number[]>,
  courses: { course_code: number; name: string }[],
): boolean {
  const normalized = name.replace(/\s*\(במקביל\)\s*$/i, '').trim();
  if (!normalized) return true;

  const direct = nameToCodes.get(normalized);
  if (direct?.some(code => codeInPassed(code, passed))) return true;

  for (const course of courses) {
    const courseName = course.name.trim();
    if (
      courseName === normalized ||
      courseName.includes(normalized) ||
      normalized.includes(courseName)
    ) {
      if (codeInPassed(course.course_code, passed)) return true;
    }
  }
  return false;
}

function prerequisitesMet(
  course: {
    prerequisites?: string;
    prerequisite_course_codes?: number[];
  },
  passed: Set<number>,
  nameToCodes: Map<string, number[]>,
  courses: { course_code: number; name: string }[],
): boolean {
  const structured = course.prerequisite_course_codes ?? [];
  if (structured.length > 0) {
    return structured.every(code => codeInPassed(code, passed));
  }

  const text = course.prerequisites?.trim();
  if (!text) return true;

  const numericCodes = text.match(/\d{4,7}/g);
  if (numericCodes?.length) {
    return numericCodes.every(c => codeInPassed(parseInt(c, 10), passed));
  }

  const items = parsePrerequisiteItems(text);
  if (items.length === 0) return true;

  return items.every(item => {
    const orParts = item.split(/\s+או\s+/).map(s => s.trim()).filter(Boolean);
    if (orParts.length > 1) {
      return orParts.some(part => prereqNameSatisfied(part, passed, nameToCodes, courses));
    }
    return prereqNameSatisfied(item, passed, nameToCodes, courses);
  });
}

const STAT_BOX_CLASS =
  'h-[4.5rem] w-full flex flex-col items-center justify-center rounded-xl border px-2 text-center';
const STAT_BOX_COMPACT_CLASS =
  'h-[3.25rem] w-full flex flex-col items-center justify-center rounded-lg border px-1.5 text-center';

function CourseStatBox({
  label,
  value,
  sub,
  tone = 'emerald',
  compact = false,
}: {
  label: string;
  value: string | number;
  sub?: string;
  tone?: 'emerald' | 'blue' | 'rose' | 'slate';
  compact?: boolean;
}) {
  const tones = {
    emerald: 'border-emerald-100 bg-emerald-50/60 text-emerald-800',
    blue: 'border-blue-100 bg-blue-50/60 text-blue-800',
    rose: 'border-rose-200 bg-rose-50 text-rose-800',
    slate: 'border-gray-200 bg-gray-50 text-gray-700',
  };
  return (
    <div className={`${compact ? STAT_BOX_COMPACT_CLASS : STAT_BOX_CLASS} ${tones[tone]}`}>
      <div className={`font-semibold opacity-80 ${compact ? 'text-[10px]' : 'text-[11px]'}`}>{label}</div>
      <div
        className={`font-bold text-gray-900 leading-tight ${compact ? 'text-base mt-0' : 'text-lg mt-0.5'}`}
      >
        {value}
      </div>
      {sub && <div className={`text-gray-500 ${compact ? 'text-[9px] mt-0' : 'text-[10px] mt-0.5'}`}>{sub}</div>}
    </div>
  );
}

function PrerequisitesBox({ prerequisites, compact }: { prerequisites: string; compact?: boolean }) {
  const items = parsePrerequisiteItems(prerequisites);
  if (items.length === 0) return null;

  return (
    <div
      className={`w-full flex flex-col items-center text-center rounded-xl border ${
        compact
          ? 'border-gray-200 bg-gray-50/90 p-2 min-h-[4rem]'
          : 'border-emerald-100 bg-emerald-50 p-4 min-h-[9rem]'
      }`}
    >
      <div className={`font-semibold text-emerald-800 ${compact ? 'text-[10px] mb-1' : 'text-sm mb-2'}`}>
        דרישות קדם
      </div>
      <div className="flex flex-wrap gap-1.5 justify-center items-center">
        {items.map((item, i) => (
          <span
            key={`${item}-${i}`}
            className={`inline-block rounded-lg border bg-white text-gray-700 leading-snug ${
              compact
                ? 'border-gray-200 text-[11px] px-2 py-1'
                : 'border-emerald-200 text-xs px-2.5 py-1.5'
            }`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function CourseExplorer() {
  const { user } = useAuth();
  const userId = user?.user_id;
  const [courses, setCourses] = useState<any[]>(() => getCacheEntry('courses') ?? []);
  const [tracks, setTracks] = useState<any[]>(() => getCacheEntry<any>('metadata')?.tracks ?? []);
  const [passedCodes, setPassedCodes] = useState<Set<number>>(() => {
    const history = userId ? getCacheEntry<any[]>(`history:${userId}`) ?? [] : [];
    return buildPassedCodes(history);
  });
  const [loading, setLoading] = useState(
    () => !(getCacheEntry('courses') && getCacheEntry('metadata')),
  );
  
  // Filters
  const [search, setSearch] = useState('');
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);
  const [noMandatoryAttendance, setNoMandatoryAttendance] = useState(false);
  const [lowWorkload, setLowWorkload] = useState(false);
  const [prereqsMetOnly, setPrereqsMetOnly] = useState(false);

  const [selectedCourse, setSelectedCourse] = useState<any>(null);
  const [reviewCourse, setReviewCourse] = useState<any>(null);

  const handleAddToList = async (course: { course_code: number; name: string }) => {
    if (!user) return;
    try {
      await api.addSchedule(user.user_id, { course_code: course.course_code });
      alert(`"${course.name}" נוסף להרשימה שלך!`);
    } catch (err) {
      console.error(err);
      alert('שגיאה בהוספה להרשימה.');
    }
  };

  useEffect(() => {
    if (!user) return;

    const cachedCourses = getCacheEntry<any[]>('courses');
    const cachedMeta = getCacheEntry<any>('metadata');
    const cachedHistory = getCacheEntry<any[]>(`history:${user.user_id}`);

    if (cachedCourses) setCourses(cachedCourses);
    if (cachedMeta?.tracks) setTracks(cachedMeta.tracks);
    if (cachedHistory) setPassedCodes(buildPassedCodes(cachedHistory));

    if (cachedCourses && cachedMeta) {
      setLoading(false);
      if (!cachedHistory) {
        api.getHistory(user.user_id).then((res) => {
          setPassedCodes(buildPassedCodes(res.data));
        }).catch(console.error);
      }
      return;
    }

    const fetchData = async () => {
      try {
        const [coursesRes, metaRes, histRes] = await Promise.all([
          api.getCourses(),
          api.getMetadata(),
          api.getHistory(user.user_id),
        ]);
        setCourses(coursesRes.data);
        if (metaRes.data?.tracks) setTracks(metaRes.data.tracks);
        setPassedCodes(buildPassedCodes(histRes.data));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  const courseInTrack = (course: { track_ids?: number[]; track_id?: number | null }, trackId: number) =>
    course.track_ids?.includes(trackId) || course.track_id === trackId;

  const nameToCodes = useMemo(() => buildCourseNameIndex(courses), [courses]);

  const filteredCourses = courses.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.course_code.toString().includes(search);

    const matchesTrack = selectedTrack ? courseInTrack(c, selectedTrack) : true;

    const matchesAttendance = noMandatoryAttendance ? !c.mandatory_attendance : true;
    const matchesWorkload = lowWorkload ? c.workload <= 3 : true;
    const matchesPrereqs = prereqsMetOnly
      ? prerequisitesMet(c, passedCodes, nameToCodes, courses)
      : true;

    return matchesSearch && matchesTrack && matchesAttendance && matchesWorkload && matchesPrereqs;
  });

  return (
    <div className="w-full min-w-0 space-y-6 animate-fade-in" dir="rtl">
      <div className="glass-panel !p-6">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-500">
          חיפוש קורסים
        </h1>
        <p className="text-gray-500 text-sm mb-6">סנן לפי מקבץ לימודים</p>

        <div className="flex flex-wrap gap-3 mb-6">
          <button
            type="button"
            onClick={() => setSelectedTrack(null)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              selectedTrack === null
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/25'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            כל המקבצים
          </button>
          {tracks.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setSelectedTrack(t.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedTrack === t.id
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/25'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              מקבץ {t.name}
            </button>
          ))}
        </div>

        <div className="flex flex-col lg:flex-row lg:items-center gap-4 bg-gray-100 p-4 rounded-xl border border-gray-200">
          <div className="relative h-9 w-full lg:max-w-xs shrink-0">
            <input
              type="text"
              placeholder="חפש לפי שם או קוד..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={`h-full w-full rounded-lg border border-gray-200 bg-white px-3 text-sm leading-9 text-gray-800 placeholder:text-gray-400 focus:outline-none ${
                search.trim() ? 'pe-[2.75rem]' : ''
              }`}
            />
            {search.trim() !== '' && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute end-1 top-1/2 flex h-5 w-10 -translate-y-1/2 items-center justify-center text-xs font-medium leading-none text-gray-300 opacity-90 outline-none select-none hover:opacity-70 active:translate-y-[-50%] active:opacity-70 focus:outline-none focus-visible:outline-none"
                aria-label="נקה חיפוש"
              >
                נקה
              </button>
            )}
          </div>
          <div className="flex flex-row flex-wrap items-center gap-x-6 gap-y-3 text-sm min-w-0 flex-1">
            <label className="inline-flex flex-row items-center gap-2 cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={noMandatoryAttendance}
                onChange={(e) => setNoMandatoryAttendance(e.target.checked)}
                className="h-4 w-4 shrink-0 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
              />
              <span className="whitespace-nowrap text-gray-600">ללא נוכחות חובה</span>
            </label>
            <label className="inline-flex flex-row items-center gap-2 cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={lowWorkload}
                onChange={(e) => setLowWorkload(e.target.checked)}
                className="h-4 w-4 shrink-0 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
              />
              <span className="whitespace-nowrap text-gray-600">עומס נמוך</span>
            </label>
            <label className="inline-flex flex-row items-center gap-2 cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={prereqsMetOnly}
                onChange={(e) => setPrereqsMetOnly(e.target.checked)}
                className="h-4 w-4 shrink-0 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
              />
              <span className="whitespace-nowrap text-gray-600">דרישות קדם מולאו</span>
            </label>
          </div>
          {!loading && (
            <p className="text-sm text-gray-600 whitespace-nowrap shrink-0">
              מציג{' '}
              <span className="font-semibold text-emerald-700">{filteredCourses.length}</span>
              {' מתוך '}
              <span className="font-semibold text-gray-800">{courses.length}</span>
              {' קורסים'}
            </p>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6 items-stretch">
          {filteredCourses.map(course => (
            <div 
              key={course.course_code} 
              onClick={() => setSelectedCourse(course)}
              className="glass-panel !p-4 flex flex-col items-center text-center h-full min-h-0 cursor-pointer hover:-translate-y-1 hover:border-blue-500/50 hover:shadow-[0_10px_30px_rgba(37,99,235,0.2)] transition-all duration-300"
            >
              <span className="inline-block text-[11px] font-mono bg-gray-100 px-2 py-0.5 rounded text-emerald-700 mb-2 shrink-0">
                {course.course_code}
              </span>
              <div className="mb-2 flex min-h-[3.25rem] w-full items-center justify-center shrink-0">
                <h3 className="text-base font-semibold leading-snug line-clamp-3 overflow-hidden w-full">
                  {course.name}
                </h3>
              </div>

              <div className="grid grid-cols-3 gap-1.5 mb-2 w-full shrink-0">
                <CourseStatBox label='נ"ז' value={course.credits} tone="emerald" compact />
                <CourseStatBox label="שעות" value={course.workload} sub="בשבוע" tone="blue" compact />
                <CourseStatBox
                  label="נוכחות"
                  value={course.mandatory_attendance ? 'חובה' : 'גמישה'}
                  tone={course.mandatory_attendance ? 'rose' : 'slate'}
                  compact
                />
              </div>

              {course.prerequisites ? (
                <div className="mb-2 w-full">
                  <PrerequisitesBox prerequisites={course.prerequisites} compact />
                </div>
              ) : (
                <div className="mb-2 w-full min-h-[4rem] rounded-lg border border-dashed border-gray-200 bg-gray-50 flex items-center justify-center text-[10px] text-gray-400">
                  אין דרישות קדם
                </div>
              )}

              {(course.day_of_week || course.start_time) && (
                <div className="text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-2 py-1 mb-2 w-full text-center">
                  {course.day_of_week || 'טרם נקבע'}
                  {course.start_time ? ` · ${course.start_time}–${course.end_time}` : ''}
                </div>
              )}
            </div>
          ))}
          {filteredCourses.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-400">
              לא נמצאו קורסים התואמים את הסינון שלך (0 מתוך {courses.length}).
            </div>
          )}
        </div>
      )}

      {selectedCourse && (
        <CourseDetailModal
          course={selectedCourse}
          onClose={() => setSelectedCourse(null)}
          onOpenReviews={() => {
            setReviewCourse(selectedCourse);
            setSelectedCourse(null);
          }}
          onAddToList={handleAddToList}
        />
      )}

      {reviewCourse && (
        <ReviewModal course={reviewCourse} onClose={() => setReviewCourse(null)} />
      )}
    </div>
  );
}
